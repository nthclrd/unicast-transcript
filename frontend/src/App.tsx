import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import { api, type Config, type Course, type Job, type PodcastList } from '@/api'
import { CoursePicker } from '@/components/CoursePicker'
import { JobProgress } from '@/components/JobProgress'
import { PodcastPicker } from '@/components/PodcastPicker'
import { SettingsDialog } from '@/components/SettingsDialog'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Toaster } from '@/components/ui/sonner'

const LAST_URL_KEY = 'unicast:lastUrl'
const OTHER_LANGUAGE = '__other__'

function readLastUrl() {
  try {
    return localStorage.getItem(LAST_URL_KEY) ?? ''
  } catch {
    return ''
  }
}

export default function App() {
  const [config, setConfig] = useState<Config | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [loggingIn, setLoggingIn] = useState(false)

  const [courses, setCourses] = useState<Course[] | null>(null)
  const [coursesError, setCoursesError] = useState('')
  const [url, setUrl] = useState(readLastUrl)
  const [loadingList, setLoadingList] = useState(false)
  const [listError, setListError] = useState('')
  const [list, setList] = useState<PodcastList | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const [outputDir, setOutputDir] = useState('')
  const [language, setLanguage] = useState('fr')
  const [customLanguage, setCustomLanguage] = useState('')
  const [doTranscribe, setDoTranscribe] = useState(true)

  const [job, setJob] = useState<Job | null>(null)

  useEffect(() => {
    api
      .getConfig()
      .then((c) => {
        setConfig(c)
        setLanguage(c.default_language)
        if (!c.user || !c.has_password) setSettingsOpen(true)
      })
      .catch(() => toast.error('Serveur injoignable. Lance `uv run python server.py`.'))
  }, [])

  const credentialsReady = !!config && !!config.user && config.has_password
  async function loadCourses() {
    try {
      setCourses(await api.listCourses())
      setCoursesError('')
      setConfig(await api.getConfig())
    } catch (err) {
      setCoursesError((err as Error).message)
      setCourses([])
    }
  }
  useEffect(() => {
    if (credentialsReady) loadCourses()
  }, [credentialsReady])

  // Suivi du traitement en cours.
  const jobId = job?.id
  const running = job?.status === 'running'
  useEffect(() => {
    if (!jobId || !running) return
    const timer = setInterval(() => {
      api.getJob(jobId).then(setJob).catch(() => {})
    }, 1000)
    return () => clearInterval(timer)
  }, [jobId, running])

  async function login() {
    setLoggingIn(true)
    try {
      setConfig(await api.login())
      toast.success('Connecté à Unicast.')
      setCourses(null)
      loadCourses()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setLoggingIn(false)
    }
  }

  async function loadPodcasts(target: string) {
    setUrl(target)
    setLoadingList(true)
    setListError('')
    setList(null)
    try {
      const result = await api.listPodcasts(target)
      setList(result)
      setSelected(new Set())
      setOutputDir(result.default_output_dir)
      try {
        localStorage.setItem(LAST_URL_KEY, target)
      } catch {
        /* stockage indisponible : pas grave */
      }
      setConfig(await api.getConfig())
    } catch (err) {
      setListError((err as Error).message)
    } finally {
      setLoadingList(false)
    }
  }

  async function start() {
    if (!list) return
    const lang = language === OTHER_LANGUAGE ? customLanguage.trim() : language
    try {
      const created = await api.createJob({
        podcasts: list.podcasts.filter((p) => selected.has(p.id)),
        student_id: list.student_id,
        output_dir: outputDir,
        language: lang || 'fr',
        transcribe: doTranscribe,
      })
      setJob(created)
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const missingCredentials = config && !credentialsReady

  return (
    <div className="min-h-svh bg-background text-foreground">
      <Toaster richColors position="top-center" />
      <div className="mx-auto grid max-w-4xl gap-6 px-4 py-8">
        <header className="flex flex-wrap items-center gap-3">
          <div className="flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">Unicast Transcriber</h1>
            <p className="text-sm text-muted-foreground">
              Télécharge et transcrit les podcasts de cours ULiège.
            </p>
          </div>
          {config && (
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={config.has_session ? 'secondary' : 'outline'}>
                {config.has_session ? 'Session active' : 'Non connecté'}
              </Badge>
              <Badge variant={config.has_deepgram ? 'secondary' : 'outline'}>
                {config.has_deepgram ? 'Deepgram OK' : 'Deepgram manquant'}
              </Badge>
              <Button variant="outline" size="sm" onClick={login} disabled={loggingIn || !!missingCredentials}>
                {loggingIn ? 'Connexion…' : 'Se reconnecter'}
              </Button>
              <Button size="sm" onClick={() => setSettingsOpen(true)}>
                Réglages
              </Button>
            </div>
          )}
        </header>

        {missingCredentials && (
          <Alert>
            <AlertTitle>Configuration requise</AlertTitle>
            <AlertDescription>
              Renseigne ton matricule et ton mot de passe ULiège dans les réglages avant de commencer.
            </AlertDescription>
          </Alert>
        )}

        <Card>
          <CardHeader>
            <CardTitle>1. Cours</CardTitle>
            <CardDescription>Choisis un de tes cours, ou colle l’adresse de sa page Unicast.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {credentialsReady && courses === null && (
              <p className="text-sm text-muted-foreground">
                Chargement de tes cours… (la première connexion peut prendre une quinzaine de secondes)
              </p>
            )}
            {coursesError && (
              <Alert variant="destructive">
                <AlertTitle>Impossible de charger tes cours</AlertTitle>
                <AlertDescription>{coursesError}</AlertDescription>
              </Alert>
            )}
            {courses && courses.length > 0 && (
              <CoursePicker
                courses={courses}
                activeUrl={url}
                disabled={loadingList}
                onPick={(c) => loadPodcasts(c.url)}
              />
            )}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                loadPodcasts(url.trim())
              }}
              className="flex gap-2"
            >
              <Input
                placeholder="https://my.unicast.uliege.be/mes_cours/…"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <Button type="submit" disabled={loadingList || !url.trim() || !!missingCredentials}>
                {loadingList ? 'Chargement…' : 'Charger'}
              </Button>
            </form>
            {loadingList && (
              <p className="text-xs text-muted-foreground">
                Si la session a expiré, la reconnexion automatique peut prendre une quinzaine de secondes.
              </p>
            )}
            {listError && (
              <Alert variant="destructive">
                <AlertTitle>Impossible de charger les podcasts</AlertTitle>
                <AlertDescription>{listError}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {list && (
          <Card>
            <CardHeader>
              <CardTitle>2. Podcasts</CardTitle>
              <CardDescription>{list.podcasts.length} podcast(s) trouvé(s). Coche ceux à traiter.</CardDescription>
            </CardHeader>
            <CardContent>
              <PodcastPicker podcasts={list.podcasts} selected={selected} onChange={setSelected} />
            </CardContent>
          </Card>
        )}

        {list && config && (
          <Card>
            <CardHeader>
              <CardTitle>3. Options</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label htmlFor="output">Dossier de sortie</Label>
                  <Input id="output" value={outputDir} onChange={(e) => setOutputDir(e.target.value)} />
                  <p className="text-xs text-muted-foreground">Relatif au dossier du projet, ou chemin absolu.</p>
                </div>
                <div className="grid gap-2">
                  <Label>Langue du cours</Label>
                  <div className="flex gap-2">
                    <Select value={language} onValueChange={setLanguage} disabled={!doTranscribe}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {config.languages.map((l) => (
                          <SelectItem key={l.code} value={l.code}>
                            {l.label} ({l.code})
                          </SelectItem>
                        ))}
                        <SelectItem value={OTHER_LANGUAGE}>Autre code…</SelectItem>
                      </SelectContent>
                    </Select>
                    {language === OTHER_LANGUAGE && (
                      <Input
                        className="w-24"
                        placeholder="it, pt…"
                        value={customLanguage}
                        onChange={(e) => setCustomLanguage(e.target.value)}
                      />
                    )}
                  </div>
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <Checkbox checked={doTranscribe} onCheckedChange={(c) => setDoTranscribe(c === true)} />
                Transcrire après le téléchargement (Deepgram)
              </label>
              <div>
                <Button onClick={start} disabled={running || selected.size === 0 || !outputDir.trim()}>
                  {running ? 'Traitement en cours…' : `Lancer (${selected.size})`}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {job && (
          <Card>
            <CardHeader>
              <CardTitle>4. Progression</CardTitle>
            </CardHeader>
            <CardContent>
              <JobProgress job={job} />
            </CardContent>
          </Card>
        )}
      </div>

      {config && (
        <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} config={config} onSaved={setConfig} />
      )}
    </div>
  )
}
