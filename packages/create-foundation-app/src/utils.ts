import pc from "picocolors";

/**
 * Logger utilities using picocolors for consistent CLI output
 */
export const logger = {
  info: (message: string) => console.log(pc.blue("ℹ"), message),
  success: (message: string) => console.log(pc.green("✔"), message),
  warning: (message: string) => console.log(pc.yellow("⚠"), message),
  error: (message: string) => console.error(pc.red("✖"), message),
  debug: (message: string) => {
    if (process.env.DEBUG) {
      console.log(pc.gray("[DEBUG]"), message);
    }
  },
};

/**
 * Error handling utilities
 */
export class CLIError extends Error {
  constructor(
    message: string,
    public readonly exitCode: number = 1,
  ) {
    super(message);
    this.name = "CLIError";
  }
}

export function handleError(error: unknown): never {
  if (error instanceof CLIError) {
    logger.error(error.message);
    process.exit(error.exitCode);
  } else if (error instanceof Error) {
    logger.error(`Unexpected error: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  } else {
    logger.error(`Unknown error: ${String(error)}`);
    process.exit(1);
  }
}
