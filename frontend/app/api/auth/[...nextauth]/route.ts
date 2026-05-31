/**
 * NextAuth.js route handler for IndoGovRAG
 * Configures Google OAuth provider with JWT session (30-day expiry)
 */

import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],

  // JWT session strategy (stateless, no database needed)
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days in seconds
  },

  // Custom pages
  pages: {
    signIn: "/",           // Use main page for sign-in
    error: "/",            // Redirect errors to home
  },

  // JWT callbacks for storing user info in token
  callbacks: {
    async jwt({ token, user, account }) {
      if (account && user) {
        token.userId = user.id;
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image;
        token.provider = account.provider;
      }
      return token;
    },

    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.userId as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.image = token.picture as string;
        session.user.provider = token.provider as string;
      }
      return session;
    },
  },
});

export { handlers, signIn, signOut, auth };
export const GET = handlers.GET;
export const POST = handlers.POST;