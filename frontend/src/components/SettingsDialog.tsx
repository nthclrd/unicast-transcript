import { useState } from 'react'
import { toast } from 'sonner'

import { api, type Config } from '@/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  config: Config
  onSaved: (config: Config) => void
}

export function SettingsDialog({ open, onOpenChange, config, onSaved }: Props) {
  const [user, setUser] = useState(config.user)
  const [password, setPassword] = useState('')
  const [deepgramKey, setDeepgramKey] = useState('')
  const [saving, setSaving] = useState(false)

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const next = await api.saveConfig({ user, password, deepgram_key: deepgramKey })
      onSaved(next)
      setPassword('')
      setDeepgramKey('')
      toast.success('Réglages enregistrés.')
      onOpenChange(false)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={save} className="grid gap-4">
          <DialogHeader>
            <DialogTitle>Réglages</DialogTitle>
            <DialogDescription>
              Stockés uniquement sur ton ordinateur, dans le fichier <code>.env</code>. Laisse un champ vide pour
              garder la valeur actuelle.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-2">
            <Label htmlFor="user">Matricule ULiège</Label>
            <Input id="user" placeholder="s1234567" value={user} onChange={(e) => setUser(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">Mot de passe ULiège</Label>
            <Input
              id="password"
              type="password"
              autoComplete="off"
              placeholder={config.has_password ? '•••••••• (enregistré)' : ''}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="deepgram">Clé API Deepgram</Label>
            <Input
              id="deepgram"
              type="password"
              autoComplete="off"
              placeholder={config.has_deepgram ? '•••••••• (enregistrée)' : ''}
              value={deepgramKey}
              onChange={(e) => setDeepgramKey(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Compte gratuit sur{' '}
              <a className="underline" href="https://console.deepgram.com/" target="_blank" rel="noreferrer">
                console.deepgram.com
              </a>
              . Nécessaire uniquement pour la transcription.
            </p>
          </div>

          <DialogFooter>
            <Button type="submit" disabled={saving}>
              {saving ? 'Enregistrement…' : 'Enregistrer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
