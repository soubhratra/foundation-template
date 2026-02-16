import { z } from "zod";

export const accountFormSchema = z.object({
  fullName: z.string().min(2, "Name is required"),
  email: z.string().email("Enter a valid email"),
  jobTitle: z.string().optional(),
  timezone: z.string().min(1, "Timezone is required"),
  productUpdates: z.boolean(),
});

export type AccountFormValues = z.infer<typeof accountFormSchema>;
