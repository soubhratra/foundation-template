import { StyleSheet, View } from "react-native";

import { Link, type Href } from "expo-router";

import { Text, theme } from "@repo/ui";

export interface AuthFooterLink {
  readonly label: string;
  readonly href: Href;
  readonly prefix?: string;
  readonly replace?: boolean;
  readonly testID?: string;
}

interface AuthFooterProps {
  readonly links: ReadonlyArray<AuthFooterLink>;
}

export function AuthFooter({ links }: AuthFooterProps) {
  if (links.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {links.map((link) => (
        <View key={`${link.label}-${JSON.stringify(link.href)}`} style={styles.linkRow}>
          {link.prefix ? (
            <Text variant="caption" style={styles.prefix}>
              {link.prefix}
            </Text>
          ) : null}
          <Link href={link.href} replace={link.replace} asChild>
            <Text variant="caption" weight="bold" style={styles.link} testID={link.testID}>
              {link.label}
            </Text>
          </Link>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: theme.spacing.xs,
  },
  linkRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: theme.spacing.xs,
  },
  prefix: {
    color: theme.colors.muted,
  },
  link: {
    color: theme.colors.primary,
  },
});
