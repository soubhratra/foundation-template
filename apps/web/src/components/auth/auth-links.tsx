import Link from "next/link";

interface AuthLinkItem {
  readonly href: string;
  readonly label: string;
  readonly prefix?: string;
}

interface AuthLinksProps {
  readonly items: ReadonlyArray<AuthLinkItem>;
}

export function AuthLinks({ items }: AuthLinksProps) {
  if (!items.length) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2 text-sm text-muted-foreground">
      {items.map((item) => (
        <p key={item.href} className="text-center">
          {item.prefix ? <span>{item.prefix} </span> : null}
          <Link href={item.href} className="font-medium text-primary hover:underline">
            {item.label}
          </Link>
        </p>
      ))}
    </div>
  );
}

export type { AuthLinkItem };
