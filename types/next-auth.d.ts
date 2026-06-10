import { DefaultSession } from "next-auth";

// Augment the Session type so `session.user.id` is available (added in the
// session callback in lib/auth.ts).
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
    } & DefaultSession["user"];
  }
}
