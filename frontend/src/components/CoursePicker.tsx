import type { Course } from '@/api'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Props = {
  courses: Course[]
  activeUrl: string
  disabled: boolean
  onPick: (course: Course) => void
}

export function CoursePicker({ courses, activeUrl, disabled, onPick }: Props) {
  // Cours avec podcasts en premier.
  const sorted = [...courses].sort((a, b) => Number(b.podcasts > 0) - Number(a.podcasts > 0))

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {sorted.map((c) => (
        <button
          key={c.id}
          type="button"
          disabled={disabled}
          onClick={() => onPick(c)}
          className={cn(
            'grid gap-1 rounded-lg border p-3 text-left transition-colors hover:bg-muted/50 disabled:pointer-events-none disabled:opacity-60',
            c.url === activeUrl && 'border-primary bg-muted/50',
            c.podcasts === 0 && 'opacity-60',
          )}
        >
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
            <Badge variant={c.podcasts > 0 ? 'secondary' : 'outline'} className="ml-auto">
              {c.podcasts} podcast{c.podcasts > 1 ? 's' : ''}
            </Badge>
          </div>
          <span className="text-sm font-medium">{c.title}</span>
          {c.professor && <span className="text-xs text-muted-foreground">{c.professor}</span>}
        </button>
      ))}
    </div>
  )
}
