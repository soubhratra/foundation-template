import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export type ActivityEntry = {
  readonly id: string;
  readonly title: string;
  readonly actor: string;
  readonly status: "success" | "warning" | "error";
  readonly time: string;
  readonly meta?: string;
};

interface ActivityTableProps {
  readonly entries: ReadonlyArray<ActivityEntry>;
  readonly dense?: boolean;
}

const statusCopy: Record<ActivityEntry["status"], { label: string; className: string }> = {
  success: {
    label: "Success",
    className: "border-emerald-500/40 text-emerald-600 dark:text-emerald-300",
  },
  warning: {
    label: "Warning",
    className: "border-amber-500/40 text-amber-600 dark:text-amber-300",
  },
  error: {
    label: "Failed",
    className: "border-rose-500/40 text-rose-600 dark:text-rose-300",
  },
};

export function ActivityTable({ entries, dense = false }: ActivityTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[45%]">Event</TableHead>
          <TableHead className="hidden md:table-cell">Actor</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">When</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {entries.map((entry) => (
          <TableRow key={entry.id} className={dense ? "text-sm" : undefined}>
            <TableCell>
              <p className="font-medium text-foreground">{entry.title}</p>
              {entry.meta ? (
                <p className="text-xs text-muted-foreground">{entry.meta}</p>
              ) : null}
            </TableCell>
            <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
              {entry.actor}
            </TableCell>
            <TableCell>
              <StatusBadge status={entry.status} />
            </TableCell>
            <TableCell className="text-right text-sm text-muted-foreground">
              {entry.time}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function StatusBadge({ status }: { readonly status: ActivityEntry["status"] }) {
  const styles = statusCopy[status];
  return (
    <Badge variant="outline" className={cn("text-xs", styles.className)}>
      {styles.label}
    </Badge>
  );
}
