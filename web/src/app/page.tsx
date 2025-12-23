// "use client";

// import { useState, useEffect } from "react";
// import { useRouter } from "next/navigation";
// import { motion } from "framer-motion";
// import { ArrowRight, Github, Sparkles, Zap, Network, ShieldCheck, LogOut, User } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
// import { toast } from "sonner";
// import { getCurrentUser, logout } from "@/app/actions";

// export default function LandingPage() {
//   const router = useRouter();
//   const [url, setUrl] = useState("");
//   const [isLoading, setIsLoading] = useState(false);
  
//   // User State
//   const [user, setUser] = useState<{ email: string; id: string } | null>(null);
//   const [authLoading, setAuthLoading] = useState(true);

//   // Check Auth on Mount
//   useEffect(() => {
//     const checkAuth = async () => {
//         try {
//             const currentUser = await getCurrentUser();
//             setUser(currentUser);
//         } catch (e) {
//             console.error("Auth check failed", e);
//         } finally {
//             setAuthLoading(false);
//         }
//     };
//     checkAuth();
//   }, []);

//   const handleAnalyze = () => {
//     if (!url.trim()) {
//       toast.error("Please enter a GitHub URL");
//       return;
//     }
//     if (!url.includes("github.com")) {
//       toast.error("Invalid GitHub URL. Must be a public repository.");
//       return;
//     }
    
//     setIsLoading(true);
//     router.push(`/chat?url=${encodeURIComponent(url)}`);
//   };

//   const handleLogout = async () => {
//       await logout();
//       setUser(null); // Clear state immediately
//       toast.success("Logged out successfully");
//       router.refresh(); // Ensure server components refresh
//   };

//   const features = [
//     {
//       icon: <Zap className="w-5 h-5 text-yellow-500" />,
//       title: "Instant Analysis",
//       description: "Ingest any public repository in seconds. No configuration required."
//     },
//     {
//       icon: <Network className="w-5 h-5 text-purple-500" />,
//       title: "Visual Architecture",
//       description: "Auto-generate interactive dependency graphs to understand structure."
//     },
//     {
//       icon: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
//       title: "Automated Audits",
//       description: "Detect security vulnerabilities and anti-patterns with AI precision."
//     }
//   ];

//   // Extract "First Name" from email (everything before @)
//   const displayName = user?.email?.split('@')[0] || "User";
//   const initial = displayName[0]?.toUpperCase() || "U";

//   return (
//     <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden selection:bg-primary/20">
      
//       {/* Background Gradients */}
//       <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
//         <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl opacity-50 mix-blend-multiply" />
//         <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-3xl opacity-50 mix-blend-multiply" />
//         <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-size-[24px_24px]" />
//       </div>

//       {/* Navbar */}
//       <nav className="relative z-10 flex items-center justify-between px-6 md:px-12 py-6 max-w-7xl mx-auto w-full">
//         <div className="flex items-center gap-3 font-bold text-xl tracking-tight cursor-pointer" onClick={() => router.push('/')}>
//           <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center border border-primary/20">
//              <img src="/logo.svg" alt="CodeSense" className="w-5 h-5" />
//           </div>
//           <span>CodeSense</span>
//         </div>

//         {/* Auth Section */}
//         <div className="flex items-center gap-4">
//            {!authLoading && (
//                user ? (
//                    <div className="flex items-center gap-3 animate-in fade-in slide-in-from-right-4 duration-500">
//                        <div className="flex items-center gap-2 px-3 py-1.5 bg-card/50 border border-border/50 rounded-full backdrop-blur-sm">
//                             <Avatar className="h-6 w-6 border border-primary/20">
//                                 <AvatarImage src="" />
//                                 <AvatarFallback className="bg-primary/10 text-primary text-[10px] font-bold">
//                                     {initial}
//                                 </AvatarFallback>
//                             </Avatar>
//                             <span className="text-sm font-medium text-muted-foreground pr-1">
//                                 {displayName}
//                             </span>
//                        </div>
                       
//                        <Button 
//                             variant="ghost" 
//                             size="icon" 
//                             onClick={handleLogout}
//                             className="h-9 w-9 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-full transition-colors"
//                             title="Sign Out"
//                        >
//                             <LogOut className="w-4 h-4" />
//                        </Button>
//                    </div>
//                ) : (
//                    <Button 
//                         variant="ghost" 
//                         size="sm" 
//                         className="font-medium hover:bg-primary/5 gap-2"
//                         onClick={() => router.push('/login')}
//                     >
//                         <User className="w-4 h-4" /> Sign In
//                    </Button>
//                )
//            )}
//         </div>
//       </nav>

//       {/* Main Content */}
//       <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 text-center max-w-5xl mx-auto w-full pt-10 pb-20">
        
//         {/* Hero Section */}
//         <motion.div
//           initial={{ opacity: 0, y: 20 }}
//           animate={{ opacity: 1, y: 0 }}
//           transition={{ duration: 0.6, ease: "easeOut" }}
//           className="flex flex-col items-center"
//         >
//           <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-medium uppercase tracking-wider mb-8 text-primary backdrop-blur-sm shadow-[0_0_15px_-3px_var(--primary)]">
//             <Sparkles className="w-3 h-3" />
//             AI-Powered Repository Intelligence
//           </div>
          
//           <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-foreground leading-[1.1]">
//             Understand any codebase <br className="hidden md:block" />
//             <span className="bg-clip-text text-transparent bg-linear-to-r from-primary via-purple-500 to-blue-500 animate-gradient-x">
//                in seconds.
//             </span>
//           </h1>
          
//           <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed">
//             Stop reading documentation. Start chatting with your code. <br />
//             Generate graphs, audit security, and refactor instantly.
//           </p>
//         </motion.div>

//         {/* Input Section */}
//         <motion.div 
//           initial={{ opacity: 0, scale: 0.95 }}
//           animate={{ opacity: 1, scale: 1 }}
//           transition={{ duration: 0.5, delay: 0.2 }}
//           className="w-full max-w-2xl relative group mb-20"
//         >
//             <div className="absolute -inset-1 bg-linear-to-r from-primary/40 to-purple-500/40 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-500" />
            
//             <div className="relative flex items-center bg-background/80 backdrop-blur-xl border border-primary/20 rounded-xl p-2 shadow-2xl">
//                 <div className="pl-4 pr-3 text-muted-foreground">
//                     <Github className="w-5 h-5" />
//                 </div>
//                 <Input 
//                     value={url}
//                     onChange={(e) => setUrl(e.target.value)}
//                     onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
//                     placeholder="https://github.com/username/repository" 
//                     className="flex-1 border-none bg-transparent shadow-none focus-visible:ring-0 h-12 text-base placeholder:text-muted-foreground/50"
//                     autoFocus
//                 />
//                 <Button 
//                     onClick={handleAnalyze} 
//                     disabled={isLoading}
//                     size="lg" 
//                     className="h-11 px-6 rounded-lg font-medium transition-all hover:scale-105 active:scale-95"
//                 >
//                     {isLoading ? (
//                         <span className="flex items-center gap-2">
//                            <Loader2 className="w-4 h-4 animate-spin" /> 
//                            Analyzing...
//                         </span>
//                     ) : (
//                         <span className="flex items-center gap-2">
//                            Analyze <ArrowRight className="w-4 h-4" />
//                         </span>
//                     )}
//                 </Button>
//             </div>
//         </motion.div>

//         {/* Feature Grid */}
//         <motion.div 
//             initial={{ opacity: 0, y: 20 }}
//             animate={{ opacity: 1, y: 0 }}
//             transition={{ delay: 0.4, duration: 0.6 }}
//             className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left"
//         >
//             {features.map((feature, i) => (
//                 <div key={i} className="group p-6 rounded-2xl bg-card/50 border border-border/50 hover:border-primary/20 hover:bg-card/80 transition-all duration-300 backdrop-blur-sm">
//                     <div className="w-10 h-10 rounded-lg bg-background border border-border flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-sm">
//                         {feature.icon}
//                     </div>
//                     <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
//                     <p className="text-sm text-muted-foreground leading-relaxed">
//                         {feature.description}
//                     </p>
//                 </div>
//             ))}
//         </motion.div>

//       </main>
//     </div>
//   );
// }

// function Loader2({ className }: { className?: string }) {
//     return (
//         <svg 
//             xmlns="http://www.w3.org/2000/svg" 
//             width="24" 
//             height="24" 
//             viewBox="0 0 24 24" 
//             fill="none" 
//             stroke="currentColor" 
//             strokeWidth="2" 
//             strokeLinecap="round" 
//             strokeLinejoin="round" 
//             className={className}
//         >
//             <path d="M21 12a9 9 0 1 1-6.219-8.56" />
//         </svg>
//     )
// }

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Github, Sparkles, Zap, Network, ShieldCheck, LogOut, User as UserIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";

// --- CLERK IMPORTS ---
import { useUser, useClerk } from "@clerk/nextjs";

export default function LandingPage() {
  const router = useRouter();
  
  // --- CLERK HOOKS ---
  const { user, isLoaded, isSignedIn } = useUser();
  const { signOut } = useClerk();

  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = () => {
    if (!url.trim()) {
      toast.error("Please enter a GitHub URL");
      return;
    }
    if (!url.includes("github.com")) {
      toast.error("Invalid GitHub URL. Must be a public repository.");
      return;
    }
    
    setIsLoading(true);
    router.push(`/chat?url=${encodeURIComponent(url)}`);
  };

  const handleLogout = async () => {
      // Use Clerk's signOut method
      await signOut();
      toast.success("Logged out successfully");
      router.refresh();
  };

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-yellow-500" />,
      title: "Instant Analysis",
      description: "Ingest any public repository in seconds. No configuration required."
    },
    {
      icon: <Network className="w-5 h-5 text-purple-500" />,
      title: "Visual Architecture",
      description: "Auto-generate interactive dependency graphs to understand structure."
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
      title: "Automated Audits",
      description: "Detect security vulnerabilities and anti-patterns with AI precision."
    }
  ];

  // Logic to display user name/email from Clerk user object
  const email = user?.primaryEmailAddress?.emailAddress;
  const displayName = user?.fullName || email?.split('@')[0] || "User";
  const initial = displayName[0]?.toUpperCase() || "U";
  const avatarUrl = user?.imageUrl;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden selection:bg-primary/20">
      
      {/* Background Gradients */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl opacity-50 mix-blend-multiply" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-3xl opacity-50 mix-blend-multiply" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-size-[24px_24px]" />
      </div>

      {/* Navbar */}
      <nav className="relative z-10 flex items-center justify-between px-6 md:px-12 py-6 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3 font-bold text-xl tracking-tight cursor-pointer" onClick={() => router.push('/')}>
          <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center border border-primary/20">
             <img src="/logo.svg" alt="CodeSense" className="w-5 h-5" />
          </div>
          <span>CodeSense</span>
        </div>

        {/* Auth Section */}
        <div className="flex items-center gap-4">
           {isLoaded && (
               isSignedIn ? (
                   <div className="flex items-center gap-3 animate-in fade-in slide-in-from-right-4 duration-500">
                       <div className="flex items-center gap-2 px-3 py-1.5 bg-card/50 border border-border/50 rounded-full backdrop-blur-sm">
                            <Avatar className="h-6 w-6 border border-primary/20">
                                <AvatarImage src={avatarUrl} />
                                <AvatarFallback className="bg-primary/10 text-primary text-[10px] font-bold">
                                    {initial}
                                </AvatarFallback>
                            </Avatar>
                            <span className="text-sm font-medium text-muted-foreground pr-1">
                                {displayName}
                            </span>
                       </div>
                       
                       <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={handleLogout}
                            className="h-9 w-9 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-full transition-colors"
                            title="Sign Out"
                       >
                            <LogOut className="w-4 h-4" />
                       </Button>
                   </div>
               ) : (
                   <Button 
                        variant="ghost" 
                        size="sm" 
                        className="font-medium hover:bg-primary/5 gap-2"
                        // Redirect to Clerk Sign In
                        onClick={() => router.push('/sign-in')}
                    >
                        <UserIcon className="w-4 h-4" /> Sign In
                   </Button>
               )
           )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 text-center max-w-5xl mx-auto w-full pt-10 pb-20">
        
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="flex flex-col items-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-medium uppercase tracking-wider mb-8 text-primary backdrop-blur-sm shadow-[0_0_15px_-3px_var(--primary)]">
            <Sparkles className="w-3 h-3" />
            AI-Powered Repository Intelligence
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-foreground leading-[1.1]">
            Understand any codebase <br className="hidden md:block" />
            <span className="bg-clip-text text-transparent bg-linear-to-r from-primary via-purple-500 to-blue-500 animate-gradient-x">
               in seconds.
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed">
            Stop reading documentation. Start chatting with your code. <br />
            Generate graphs, audit security, and refactor instantly.
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="w-full max-w-2xl relative group mb-20"
        >
            <div className="absolute -inset-1 bg-linear-to-r from-primary/40 to-purple-500/40 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-500" />
            
            <div className="relative flex items-center bg-background/80 backdrop-blur-xl border border-primary/20 rounded-xl p-2 shadow-2xl">
                <div className="pl-4 pr-3 text-muted-foreground">
                    <Github className="w-5 h-5" />
                </div>
                <Input 
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                    placeholder="https://github.com/username/repository" 
                    className="flex-1 border-none bg-transparent shadow-none focus-visible:ring-0 h-12 text-base placeholder:text-muted-foreground/50"
                    autoFocus
                />
                <Button 
                    onClick={handleAnalyze} 
                    disabled={isLoading}
                    size="lg" 
                    className="h-11 px-6 rounded-lg font-medium transition-all hover:scale-105 active:scale-95"
                >
                    {isLoading ? (
                        <span className="flex items-center gap-2">
                           <Loader2 className="w-4 h-4 animate-spin" /> 
                           Analyzing...
                        </span>
                    ) : (
                        <span className="flex items-center gap-2">
                           Analyze <ArrowRight className="w-4 h-4" />
                        </span>
                    )}
                </Button>
            </div>
        </motion.div>

        {/* Feature Grid */}
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left"
        >
            {features.map((feature, i) => (
                <div key={i} className="group p-6 rounded-2xl bg-card/50 border border-border/50 hover:border-primary/20 hover:bg-card/80 transition-all duration-300 backdrop-blur-sm">
                    <div className="w-10 h-10 rounded-lg bg-background border border-border flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-sm">
                        {feature.icon}
                    </div>
                    <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        {feature.description}
                    </p>
                </div>
            ))}
        </motion.div>

      </main>
    </div>
  );
}