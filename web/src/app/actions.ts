// "use server";

// import { prisma } from "@/lib/db";
// import { revalidatePath } from "next/cache";
// import { getSession, encrypt } from "@/lib/auth";
// import { cookies } from "next/headers";
// import bcrypt from "bcryptjs";
// import { redirect } from "next/navigation";

// // --- AUTH ACTIONS ---

// export async function getCurrentUser() {
//   const session = await getSession();
//   return session?.user || null;
// }

// export async function login(formData: FormData) {
//   const email = formData.get("email") as string;
//   const password = formData.get("password") as string;

//   if (!email || !password) return { error: "Missing fields" };

//   try {
//     const user = await prisma.user.findUnique({ where: { email } });
    
//     if (!user || !(await bcrypt.compare(password, user.password))) {
//         return { error: "Invalid credentials" };
//     }

//     const expires = new Date(Date.now() + 24 * 60 * 60 * 1000);
//     const session = await encrypt({ user: { id: user.id, email: user.email }, expires });
//     (await cookies()).set("session", session, { expires, httpOnly: true });
//   } catch (e) {
//       return { error: "Login failed" };
//   }
  
//   redirect("/");
// }

// export async function register(formData: FormData) {
//   const email = formData.get("email") as string;
//   const password = formData.get("password") as string;

//   if (!email || !password) return { error: "Missing fields" };

//   try {
//     const existing = await prisma.user.findUnique({ where: { email } });
//     if (existing) return { error: "User already exists" };

//     const hashedPassword = await bcrypt.hash(password, 10);
//     const user = await prisma.user.create({
//         data: { email, password: hashedPassword }
//     });

//     const expires = new Date(Date.now() + 24 * 60 * 60 * 1000);
//     const session = await encrypt({ user: { id: user.id, email: user.email }, expires });
//     (await cookies()).set("session", session, { expires, httpOnly: true });
//   } catch (e) {
//       return { error: "Registration failed" };
//   }

//   redirect("/");
// }

// export async function logout() {
//   (await cookies()).set("session", "", { expires: new Date(0) });
//   return { success: true };
// }

// // --- REPOSITORY ACTIONS ---

// export async function getOrCreateRepository(url: string, name: string) {
//   try {
//     let repo = await prisma.repository.findUnique({ where: { url } });
//     if (!repo) {
//       repo = await prisma.repository.create({ data: { url, name } });
//     }
//     return repo;
//   } catch (error) {
//     console.error("Failed to get/create repo:", error);
//     return null;
//   }
// }

// // --- SESSION & MESSAGE ACTIONS ---

// export async function getChatSessions(repositoryId: string) {
//   const user = await getCurrentUser();
//   if (!user) return [];

//   try {
//     return await prisma.chatSession.findMany({
//       where: { repositoryId, userId: user.id },
//       orderBy: { updatedAt: "desc" },
//       include: { _count: { select: { messages: true } } }
//     });
//   } catch (error) {
//     return [];
//   }
// }

// export async function deleteChatSession(sessionId: string) {
//     try {
//         const user = await getCurrentUser();
//         if (!user) return false;
//         await prisma.chatSession.delete({ where: { id: sessionId, userId: user.id } });
//         revalidatePath("/");
//         return true;
//     } catch (e) {
//         return false;
//     }
// }

// export async function getChatMessages(sessionId: string) {
//   try {
//     return await prisma.message.findMany({
//       where: { chatSessionId: sessionId },
//       orderBy: { createdAt: "asc" },
//     });
//   } catch (error) {
//     return [];
//   }
// }

// export async function saveMessage(
//   sessionId: string | null, // Allow null for new sessions
//   role: "user" | "assistant", 
//   content: string,
//   repositoryId?: string // Required if creating new session
// ) {
//   const user = await getCurrentUser();
//   let currentSessionId = sessionId;

//   // 1. Lazy Creation: Create Session if it doesn't exist
//   if (!currentSessionId) {
//       if (!repositoryId) return { error: "Missing repository ID" };
      
//       try {
//           const newSession = await prisma.chatSession.create({
//               data: {
//                   repositoryId,
//                   title: role === "user" ? content.slice(0, 40) + (content.length > 40 ? "..." : "") : "New Chat",
//                   userId: user?.id || null,
//               }
//           });
//           currentSessionId = newSession.id;
//       } catch (e) {
//           return { error: "Failed to create session" };
//       }
//   }

//   // 2. Limit Check (Anonymous)
//   if (role === "user" && !user) {
//       const count = await prisma.message.count({
//           where: { chatSessionId: currentSessionId, role: "user" }
//       });
//       if (count >= 3) return { error: "LIMIT_REACHED" };
//   }

//   // 3. Save Message
//   try {
//     const message = await prisma.message.create({
//       data: {
//         chatSessionId: currentSessionId,
//         role,
//         content,
//       },
//     });

//     // Update timestamp
//     await prisma.chatSession.update({
//         where: { id: currentSessionId },
//         data: { updatedAt: new Date() }
//     });

//     return { message, sessionId: currentSessionId }; // Return new ID
//   } catch (error) {
//     return null;
//   }
// }


"use server";

import { prisma } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { getSession, encrypt } from "@/lib/auth";
import { cookies } from "next/headers";
import bcrypt from "bcryptjs";
import { redirect } from "next/navigation";

// --- AUTH ACTIONS ---

export async function getCurrentUser() {
  const session = await getSession();
  return session?.user || null;
}

export async function login(formData: FormData) {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!email || !password) return { error: "Missing fields" };

  try {
    const user = await prisma.user.findUnique({ where: { email } });
    
    if (!user || !(await bcrypt.compare(password, user.password))) {
        return { error: "Invalid credentials" };
    }

    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000);
    const session = await encrypt({ user: { id: user.id, email: user.email }, expires });
    (await cookies()).set("session", session, { expires, httpOnly: true });
  } catch (e) {
      return { error: "Login failed" };
  }
  
  redirect("/");
}

export async function register(formData: FormData) {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!email || !password) return { error: "Missing fields" };

  try {
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) return { error: "User already exists" };

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = await prisma.user.create({
        data: { email, password: hashedPassword }
    });

    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000);
    const session = await encrypt({ user: { id: user.id, email: user.email }, expires });
    (await cookies()).set("session", session, { expires, httpOnly: true });
  } catch (e) {
      return { error: "Registration failed" };
  }

  redirect("/");
}

export async function logout() {
  (await cookies()).set("session", "", { expires: new Date(0) });
  return { success: true };
}

// --- REPOSITORY ACTIONS ---

export async function getOrCreateRepository(url: string, name: string) {
  try {
    let repo = await prisma.repository.findUnique({ where: { url } });
    if (!repo) {
      repo = await prisma.repository.create({ data: { url, name } });
    }
    return repo;
  } catch (error) {
    console.error("Failed to get/create repo:", error);
    return null;
  }
}

export async function deleteRepository(repoId: string) {
    const user = await getCurrentUser();
    if (!user) return { error: "Unauthorized" };

    try {
        // 1. Delete from PostgreSQL (Brain A)
        await prisma.repository.delete({ where: { id: repoId } });

        // 2. Trigger Background Cleanup (Brain B Sync)
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        await fetch(`${API_URL}/repo/${repoId}`, { method: "DELETE" });

        revalidatePath("/");
        return { success: true };
    } catch (e) {
        console.error("Delete Repo Error:", e);
        return { error: "Failed to delete repository" };
    }
}

// --- SESSION & MESSAGE ACTIONS ---

export async function getChatSessions(repositoryId: string) {
  const user = await getCurrentUser();
  if (!user) return [];

  try {
    return await prisma.chatSession.findMany({
      where: { repositoryId, userId: user.id },
      orderBy: { updatedAt: "desc" },
      include: { _count: { select: { messages: true } } }
    });
  } catch (error) {
    return [];
  }
}

export async function deleteChatSession(sessionId: string) {
    try {
        const user = await getCurrentUser();
        if (!user) return false;
        await prisma.chatSession.delete({ where: { id: sessionId, userId: user.id } });
        revalidatePath("/");
        return true;
    } catch (e) {
        return false;
    }
}

export async function getChatMessages(sessionId: string) {
  try {
    return await prisma.message.findMany({
      where: { chatSessionId: sessionId },
      orderBy: { createdAt: "asc" },
    });
  } catch (error) {
    return [];
  }
}

export async function saveMessage(
  sessionId: string | null, // Allow null for new sessions
  role: "user" | "assistant", 
  content: string,
  repositoryId?: string // Required if creating new session
) {
  const user = await getCurrentUser();
  let currentSessionId = sessionId;

  // 1. Lazy Creation: Create Session if it doesn't exist
  if (!currentSessionId) {
      if (!repositoryId) return { error: "Missing repository ID" };
      
      try {
          const newSession = await prisma.chatSession.create({
              data: {
                  repositoryId,
                  title: role === "user" ? content.slice(0, 40) + (content.length > 40 ? "..." : "") : "New Chat",
                  userId: user?.id || null,
              }
          });
          currentSessionId = newSession.id;
      } catch (e) {
          return { error: "Failed to create session" };
      }
  }

  // --- TYPE FIX: Ensure we have a string ID ---
  if (!currentSessionId) {
      return { error: "Failed to initialize session ID" };
  }

  // 2. Limit Check (Anonymous)
  if (role === "user" && !user) {
      const count = await prisma.message.count({
          where: { chatSessionId: currentSessionId, role: "user" }
      });
      if (count >= 3) return { error: "LIMIT_REACHED" };
  }

  // 3. Save Message
  try {
    const message = await prisma.message.create({
      data: {
        chatSessionId: currentSessionId,
        role,
        content,
      },
    });

    // Update timestamp
    await prisma.chatSession.update({
        where: { id: currentSessionId },
        data: { updatedAt: new Date() }
    });

    return { message, sessionId: currentSessionId }; // Return new ID
  } catch (error) {
    return null;
  }
}