import { z } from "zod";

const EMAIL_MESSAGE = "Enter a valid email address.";
const PASSWORD_MESSAGE = "Password must be at least 8 characters.";

const emailField = z
  .string({ required_error: EMAIL_MESSAGE })
  .trim()
  .min(1, EMAIL_MESSAGE)
  .email(EMAIL_MESSAGE)
  .max(320, "Email must be 320 characters or fewer.");

const passwordField = z
  .string({ required_error: PASSWORD_MESSAGE })
  .min(8, PASSWORD_MESSAGE)
  .max(128, "Password must be 128 characters or fewer.");

const confirmPasswordRefinement = <SchemaType extends z.ZodTypeAny>(
  schema: SchemaType,
  passwordKey: keyof z.infer<SchemaType>,
  confirmKey: keyof z.infer<SchemaType>,
) =>
  schema.superRefine((values, ctx) => {
    if (values[passwordKey] !== values[confirmKey]) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [confirmKey as string],
        message: "Passwords must match.",
      });
    }
  });

export const loginSchema = z.object({
  email: emailField,
  password: passwordField,
  remember: z.boolean().default(false),
});

export const signupSchema = confirmPasswordRefinement(
  z.object({
    name: z
      .string({ required_error: "Name is required." })
      .trim()
      .min(1, "Name is required.")
      .max(255, "Name must be 255 characters or fewer."),
    email: emailField,
    password: passwordField,
    confirmPassword: z
      .string({ required_error: "Confirm your password." })
      .min(1, "Confirm your password."),
    marketingOptIn: z.boolean().default(false),
  }),
  "password",
  "confirmPassword",
);

export const passwordResetSchema = z.object({
  email: emailField,
});

export const passwordChangeSchema = confirmPasswordRefinement(
  z.object({
    currentPassword: passwordField.describe("Existing account password."),
    newPassword: passwordField.describe("New password with minimum length 8."),
    confirmPassword: z
      .string({ required_error: "Confirm your new password." })
      .min(1, "Confirm your new password."),
  }).superRefine((values, ctx) => {
    if (values.currentPassword === values.newPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["newPassword"],
        message: "New password must be different from current password.",
      });
    }
  }),
  "newPassword",
  "confirmPassword",
);

export const emailVerificationSchema = z.object({
  key: z
    .string({ required_error: "Verification key is required." })
    .trim()
    .min(1, "Verification key is required.")
    .max(128, "Verification key must be 128 characters or fewer."),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type SignupInput = z.infer<typeof signupSchema>;
export type PasswordResetInput = z.infer<typeof passwordResetSchema>;
export type PasswordChangeInput = z.infer<typeof passwordChangeSchema>;
export type EmailVerificationInput = z.infer<typeof emailVerificationSchema>;
