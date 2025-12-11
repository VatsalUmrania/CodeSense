import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

// Fail hard if secret missing in production
const SECRET_KEY = process.env.JWT_SECRET;
if (!SECRET_KEY && process.env.NODE_ENV === "production") {
  throw new Error("JWT_SECRET is not defined");
}

const key = new TextEncoder().encode(SECRET_KEY || "dev-fallback-secret-do-not-use-in-prod");

export async function encrypt(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("24h")
    .sign(key);
}

export async function decrypt(token: string): Promise<any> {
  try {
    const { payload } = await jwtVerify(token, key, {
      algorithms: ["HS256"],
    });
    return payload;
  } catch {
    return null;
  }
}

export async function getSession() {
  const cookieStore = cookies();
  const sessionToken = (await cookieStore).get("session")?.value;
  if (!sessionToken) return null;

  return await decrypt(sessionToken);
}

export async function updateSession(request: NextRequest) {
  const sessionToken = request.cookies.get("session")?.value;
  if (!sessionToken) return;

  const parsed = await decrypt(sessionToken);
  if (!parsed) return;

  const refreshedToken = await encrypt({ ...parsed });

  const res = NextResponse.next();
  res.cookies.set({
    name: "session",
    value: refreshedToken,
    httpOnly: true,
    path: "/",
    maxAge: 60 * 60 * 24, // 24h
  });

  return res;
}
