import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import type {
  DefaultValues,
  FieldPath,
  FieldValues,
  UseFormProps,
} from "react-hook-form";

type SchemaValues<TSchema extends z.ZodTypeAny> = z.infer<TSchema>;

type CreateFormOptions<TSchema extends z.ZodTypeAny> = Omit<
  UseFormProps<SchemaValues<TSchema>>,
  "resolver" | "defaultValues"
> & {
  defaultValues?: Partial<SchemaValues<TSchema>>;
};

export function createZodFormOptions<TSchema extends z.ZodTypeAny>(
  schema: TSchema,
  options: CreateFormOptions<TSchema> = {},
): UseFormProps<SchemaValues<TSchema>> {
  const {
    defaultValues,
    mode = "onSubmit",
    reValidateMode = "onChange",
    ...rest
  } = options;

  return {
    mode,
    reValidateMode,
    resolver: zodResolver(schema),
    defaultValues: normalizeDefaultValues(schema, defaultValues),
    ...rest,
  };
}

export function buildFormDefaults<
  TSchema extends z.ZodTypeAny,
  TValue extends SchemaValues<TSchema> = SchemaValues<TSchema>,
>(
  schema: TSchema,
  overrides: Partial<TValue> = {},
): TValue {
  if (isZodObject(schema)) {
    const base = schema.partial().parse({}) as TValue;
    return { ...base, ...overrides };
  }

  return { ...overrides } as TValue;
}

export function createFieldErrorMap<TFieldValues extends FieldValues>(
  errors: Partial<Record<FieldPath<TFieldValues>, string>>,
) {
  const map: Record<string, string> = {};
  for (const field of Object.keys(errors) as Array<FieldPath<TFieldValues>>) {
    const message = errors[field];
    if (typeof message === "string" && message.length > 0) {
      map[field] = message;
    }
  }
  return map;
}

function normalizeDefaultValues<TSchema extends z.ZodTypeAny>(
  schema: TSchema,
  overrides?: Partial<SchemaValues<TSchema>>,
): DefaultValues<SchemaValues<TSchema>> {
  if (!overrides || Object.keys(overrides).length === 0) {
    return buildFormDefaults(schema) as DefaultValues<SchemaValues<TSchema>>;
  }

  return buildFormDefaults(schema, overrides) as DefaultValues<SchemaValues<TSchema>>;
}

const isZodObject = (
  schema: z.ZodTypeAny,
): schema is z.ZodObject<z.ZodRawShape, "strip", z.ZodTypeAny, any, any> => {
  return schema instanceof z.ZodObject;
};
