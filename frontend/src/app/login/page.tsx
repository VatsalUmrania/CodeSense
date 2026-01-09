"use client";

import { useState } from "react";
import { login, register } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (formData: FormData) => {
      setLoading(true);
      const action = isLogin ? login : register;
      
      const result = await action(formData);
      
      if (result?.error) {
          toast.error(result.error);
          setLoading(false);
      } else {
          // Redirect happens server-side on success
      }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-muted/20">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>{isLogin ? "Welcome Back" : "Create Account"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form action={handleSubmit} className="grid gap-4">
             <div className="grid gap-2">
                <label htmlFor="email">Email</label>
                <Input id="email" name="email" type="email" required placeholder="m@example.com"/>
             </div>
             <div className="grid gap-2">
                <label htmlFor="password">Password</label>
                <Input id="password" name="password" type="password" required />
             </div>
             <Button disabled={loading} type="submit" className="w-full">
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLogin ? "Login" : "Sign Up"}
             </Button>
          </form>
        </CardContent>
        <CardFooter>
            <Button variant="link" onClick={() => setIsLogin(!isLogin)} className="w-full text-xs text-muted-foreground">
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Login"}
            </Button>
        </CardFooter>
      </Card>
    </div>
  );
}