import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { User, Lock, LogIn, AlertCircle, Loader2 } from "lucide-react";
import { loginAction } from "@/actions/auth";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get("email");
    const password = formData.get("password");
    
    const result = await loginAction(email, password);

    if (result.success) {
      if (login) login(result.user);
      navigate("/");
    } else {
      setError(result.error);
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background relative overflow-hidden font-sans pt-28">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]" />

      <div className="relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10">
        
        <div className="max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700">
          
          <div className="text-center mb-10">
            <div className="flex justify-center mb-6">
              <div className="w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center">
                <LogIn className="w-7 h-7 text-primary" />
              </div>
            </div>
            <h1 className="text-5xl font-serif font-black mb-3 text-primary tracking-tighter">Welcome</h1>
            <p className="text-primary/40 font-bold italic text-sm">Access your Bukoo account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1">Email Address</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors" />
                </div>
                <input 
                  type="email" 
                  name="email"
                  required
                  placeholder="Enter your email"
                  className="w-full pl-12 pr-4 py-4 md:py-5 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1">Password</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors" />
                </div>
                <input 
                  type="password" 
                  name="password"
                  required
                  placeholder="Enter your password"
                  className="w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-medium"
                />
              </div>
            </div>

            <div className="flex items-center justify-between px-1">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" className="w-5 h-5 rounded-lg border-primary/10 text-primary focus:ring-primary/20" />
                <span className="text-xs font-bold text-primary/40 group-hover:text-primary transition-colors">Remember me</span>
              </label>
              <Link to="#" className="text-xs font-black text-primary hover:underline">Forgot Password?</Link>
            </div>

            {error && (
              <div className="bg-destructive/5 border border-destructive/10 rounded-2xl p-4 flex items-start gap-3 animate-in slide-in-from-top-2 duration-300">
                <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
                <p className="text-xs font-bold text-destructive leading-relaxed">{error}</p>
              </div>
            )}

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  <span>Login Account Now</span>
                </>
              )}
            </button>
          </form>

          <p className="text-center text-xs text-primary/40 font-bold mt-10">
            Don't have an account? <Link to="/register" className="text-primary font-black hover:underline uppercase tracking-widest ml-1">Register Now</Link>
          </p>
        </div>
        
        <div className="mt-20">
            <Link to="/" className="text-xs font-bold uppercase tracking-widest opacity-20 hover:opacity-100 transition-opacity">Back to Home</Link>
        </div>
      </div>
    </main>
  );
}
