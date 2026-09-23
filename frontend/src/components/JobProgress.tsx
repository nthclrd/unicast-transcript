import { useState } from 'react'
import { toast } from 'sonner'

import { api, type ItemStatus, type Job } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'

const STATUS: Record<ItemStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: { label: 'En attente', variant: 'outline' },
  downloading: { label: 'Téléchargement…', variant: 'secondary' },
  transcribing: { label: 'Transcription…', variant: 'secondary' },
  done: { label: 'Terminé', variant: 'default' },
  error: { label: 'Erreur', variant: 'destructive' },
  cancelled: { label: 'Annulé', variant: 'outline' },
}

export function JobProgress({ job }: { job: Job }) {
  const [transcript, setTranscript] = useState<{ title: string; text: string } | null>(null)

  const finished = job.items.filter((i) => ['done', 'error', 'cancelled'].includes(i.status)).length
  const running = job.status === 'running'

  async function run(action: () => Promise<unknown>) {
    try {
      await action()
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  async function showTranscript(title: string, path: string) {
    await run(async () => setTranscript({ title, text: (await api.readTranscript(path)).text }))
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <div className="flex items-center justify-between text-sm">
          <span>
            {finished} / {job.items.length} traité(s)
          </span>
          <div className="flex gap-2">
            {running && (
              <Button variant="outline" size="sm" onClick={() => run(() => api.cancelJob(job.id))}>
                Annuler
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => run(() => api.open(job.output_dir))}>
              Ouvrir le dossier
            </Button>
          </div>
        </div>
        <Progress value={(finished / job.items.length) * 100} />
        <p className="truncate text-xs text-muted-foreground" title={job.output_dir}>
          {job.output_dir}
        </p>
      </div>

      <ul className="divide-y rounded-lg border">
        {job.items.map((item) => {
          const status = STATUS[item.status]
          const lastLog = item.log.at(-1)
          return (
            <li key={item.podcast.id} className="grid gap-1 px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="flex-1 text-sm">{item.podcast.title}</span>
                {item.txt && (
                  <Button variant="ghost" size="sm" onClick={() => showTranscript(item.podcast.title, item.txt!)}>
                    Voir le texte
                  </Button>
                )}
                <Badge variant={status.variant}>{status.label}</Badge>
              </div>
              {item.status === 'error' && lastLog && <p className="text-xs text-destructive">{lastLog}</p>}
            </li>
          )
        })}
      </ul>

      <Dialog open={transcript !== null} onOpenChange={(open) => !open && setTranscript(null)}>
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{transcript?.title}</DialogTitle>
            <DialogDescription>Transcript généré par Deepgram.</DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[60vh] rounded-lg border p-4">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{transcript?.text}</p>
          </ScrollArea>
          <DialogFooter>
            <Button
              onClick={() =>
                run(async () => {
                  await navigator.clipboard.writeText(transcript?.text ?? '')
                  toast.success('Texte copié.')
                })
              }
            >
              Copier
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
