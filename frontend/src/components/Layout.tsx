import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Compass, Target, BarChart3, Map, Award, Code2, FolderGit2,
  MessageSquare, Users, LogOut, Sparkles, Menu, X,
  Shield, UserCog, FileQuestion, Database, TrendingUp,
} from 'lucide-react';

const studentNav = [
  { name: 'Dashboard', path: '/dashboard', icon: Compass },
  { name: 'Career Path', path: '/career-goal', icon: Target },
  { name: 'Skill Gap', path: '/skill-gap', icon: BarChart3 },
  { name: 'Roadmap', path: '/roadmap', icon: Map },
  { name: 'Practice Lab', path: '/practice', icon: Code2 },
  { name: 'Assessments', path: '/assessments', icon: Award },
  { name: 'Projects', path: '/projects', icon: FolderGit2 },
  { name: 'AI Mentor', path: '/ai-mentor', icon: Sparkles },
  { name: 'My Mentor', path: '/my-mentor', icon: Users },
];

const mentorNav = [
  { name: 'Dashboard', path: '/mentor/dashboard', icon: Compass },
  { name: 'Mentees', path: '/mentor/mentees', icon: Users },
  { name: 'Doubt Queue', path: '/mentor/doubts', icon: MessageSquare },
  { name: 'Project Reviews', path: '/mentor/projects', icon: FolderGit2 },
  { name: 'Analytics', path: '/mentor/analytics', icon: TrendingUp },
];

const adminNav = [
  { name: 'Overview', path: '/admin/dashboard', icon: Shield },
  { name: 'Users', path: '/admin/users', icon: UserCog },
  { name: 'Mentors', path: '/admin/mentors', icon: Users },
  { name: 'Question Bank', path: '/admin/questions', icon: FileQuestion },
  { name: 'Coding Problems', path: '/admin/coding-problems', icon: Database },
  { name: 'Analytics', path: '/admin/analytics', icon: TrendingUp },
];

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, profile, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = user?.role === 'admin' ? adminNav : user?.role === 'mentor' ? mentorNav : studentNav;

  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/dashboard') return true;
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-slate-800 bg-slate-900/50 fixed h-full z-40">
        <div className="p-5 border-b border-slate-800">
          <Link to="/dashboard" className="flex items-center space-x-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white block">Skill Pilot</span>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Career Readiness</span>
            </div>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4.5 h-4.5 ${active ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-9 h-9 rounded-full bg-indigo-950 border border-indigo-700 flex items-center justify-center text-xs font-semibold text-indigo-300 shrink-0">
              {user?.username?.substring(0, 2).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{user?.username}</p>
              <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
            </div>
            <button onClick={handleLogout} title="Log Out" className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <span className="text-lg font-bold text-white">Skill Pilot</span>
              <button onClick={() => setSidebarOpen(false)} className="p-1 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                return (
                  <Link key={item.path} to={item.path} onClick={() => setSidebarOpen(false)}
                    className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                      active ? 'bg-indigo-600/15 text-indigo-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}>
                    <Icon className="w-4.5 h-4.5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="p-3 border-t border-slate-800">
              <button onClick={handleLogout} className="flex items-center gap-2 text-slate-400 hover:text-rose-400 text-sm">
                <LogOut className="w-4 h-4" /> Logout
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-1.5 text-slate-400 hover:text-white">
                <Menu className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400 lg:hidden" />
                <span className="text-sm font-semibold text-slate-200 lg:hidden">Skill Pilot</span>
                {profile?.target_role_name && (
                  <span className="hidden lg:flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                    Target: <strong className="text-slate-100">{profile.target_role_name}</strong>
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500 hidden sm:block">{user?.username}</span>
              <div className="w-8 h-8 rounded-full bg-indigo-950 border border-indigo-700 flex items-center justify-center text-xs font-semibold text-indigo-300">
                {user?.username?.substring(0, 2).toUpperCase() || 'U'}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>

        <footer className="border-t border-slate-800/60 py-4 text-center text-xs text-slate-500">
          Skill Pilot AI — Adaptive Career Readiness Platform
        </footer>
      </div>
    </div>
  );
};
