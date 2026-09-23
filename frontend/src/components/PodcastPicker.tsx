import { useMemo, useState } from 'react'

import type { Podcast } from '@/api'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'

type Props = {
  podcasts: Podcast[]
  selected: Set<string>
  onChange: (selected: Set<string>) => void
}

const yearOf = (date: string) => date.match(/\d{4}/)?.[0] ?? ''

export function PodcastPicker({ podcasts, selected, onChange }: Props) {
  const [query, setQuery] = useState('')

  const years = useMemo(
    () => [...new Set(podcasts.map((p) => yearOf(p.date)).filter(Boolean))].sort(),
    [podcasts],
  )
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return q ? podcasts.filter((p) => `${p.title} ${p.date}`.toLowerCase().includes(q)) : podcasts
  }, [podcasts, query])

  const allVisibleSelected = visible.length > 0 && visible.every((p) => selected.has(p.id))

  function toggle(id: string, checked: boolean) {
    const next = new Set(selected)
    if (checked) next.add(id)
    else next.delete(id)
    onChange(next)
  }

  function setMany(ids: string[], checked: boolean) {
    const next = new Set(selected)
    ids.forEach((id) => (checked ? next.add(id) : next.delete(id)))
    onChange(next)
  }

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          className="max-w-xs"
          placeholder="Filtrer par titre ou date…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMany(visible.map((p) => p.id), !allVisibleSelected)}
        >
          {allVisibleSelected ? 'Tout désélectionner' : 'Tout sélectionner'}
        </Button>
        {years.length > 1 &&
          years.map((year) => (
            <Button
              key={year}
              variant="ghost"
              size="sm"
              onClick={() => setMany(podcasts.filter((p) => yearOf(p.date) === year).map((p) => p.id), true)}
            >
              + {year}
            </Button>
          ))}
        <span className="ml-auto text-sm text-muted-foreground">
          {selected.size} / {podcasts.length} sélectionné(s)
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto rounded-lg border">
        <ul className="divide-y">
          {visible.map((p, i) => (
            <li key={p.id}>
              <label className="flex cursor-pointer items-center gap-3 px-3 py-2 hover:bg-muted/50">
                <Checkbox checked={selected.has(p.id)} onCheckedChange={(c) => toggle(p.id, c === true)} />
                <span className="w-8 text-right text-xs tabular-nums text-muted-foreground">{i + 1}</span>
                <span className="flex-1 text-sm">{p.title}</span>
                {p.date && <span className="text-xs tabular-nums text-muted-foreground">{p.date}</span>}
              </label>
            </li>
          ))}
          {visible.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">Aucun résultat.</li>
          )}
        </ul>
      </div>
    </div>
  )
}
