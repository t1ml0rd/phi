import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster } from "sonner";
import { toast } from "sonner";
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Separator } from "./components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animated Background Component
const AnimatedBackground = () => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const generateParticles = () => {
      const newParticles = [];
      for (let i = 0; i < 50; i++) {
        newParticles.push({
          id: i,
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight,
          size: Math.random() * 3 + 1,
          speedX: (Math.random() - 0.5) * 0.5,
          speedY: (Math.random() - 0.5) * 0.5,
          opacity: Math.random() * 0.5 + 0.1
        });
      }
      setParticles(newParticles);
    };

    generateParticles();
    const interval = setInterval(() => {
      setParticles(prev => prev.map(particle => ({
        ...particle,
        x: (particle.x + particle.speedX + window.innerWidth) % window.innerWidth,
        y: (particle.y + particle.speedY + window.innerHeight) % window.innerHeight
      })));
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="absolute w-1 h-1 bg-cyan-400 rounded-full"
          style={{
            left: particle.x,
            top: particle.y,
            opacity: particle.opacity,
            width: particle.size,
            height: particle.size,
            boxShadow: `0 0 ${particle.size * 2}px rgba(0, 229, 255, 0.6)`
          }}
        />
      ))}
    </div>
  );
};

// Landing Page Component
const LandingPage = ({ onStart }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex flex-col items-center justify-center relative overflow-hidden">
      <AnimatedBackground />
      
      <div className="text-center space-y-8 z-10 max-w-4xl mx-auto px-6">
        <div className="space-y-4">
          <h1 className="text-7xl md:text-8xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent animate-pulse">
            AI Physics Lab
          </h1>
          <div className="h-1 w-32 bg-gradient-to-r from-cyan-400 to-violet-400 mx-auto rounded-full"></div>
        </div>
        
        <p className="text-2xl md:text-3xl text-slate-300 font-light leading-relaxed">
          Learn, test, and amaze — 
          <span className="text-cyan-400 font-semibold"> physics powered by AI</span>
        </p>
        
        <div className="grid md:grid-cols-3 gap-6 mt-12">
          <Card className="bg-slate-800/50 border-cyan-400/30 backdrop-blur-sm hover:border-cyan-400 transition-all duration-300">
            <CardHeader>
              <CardTitle className="text-cyan-400 text-xl">🧠 AI Generated</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">Unlimited physics problems created by advanced AI</p>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-violet-400/30 backdrop-blur-sm hover:border-violet-400 transition-all duration-300">
            <CardHeader>
              <CardTitle className="text-violet-400 text-xl">⚡ Instant Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">Get immediate explanations and step-by-step solutions</p>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-cyan-400/30 backdrop-blur-sm hover:border-cyan-400 transition-all duration-300">
            <CardHeader>
              <CardTitle className="text-cyan-400 text-xl">📊 Visual Learning</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300">Interactive diagrams and mathematical visualization</p>
            </CardContent>
          </Card>
        </div>
        
        <div className="mt-16">
          <Button 
            onClick={onStart}
            size="lg"
            className="bg-gradient-to-r from-cyan-500 to-violet-500 hover:from-cyan-600 hover:to-violet-600 text-white text-xl px-12 py-6 rounded-full shadow-2xl hover:shadow-cyan-500/25 transition-all duration-300 transform hover:scale-105"
            data-testid="generate-task-btn"
          >
            Generate Physics Task
          </Button>
        </div>
        
        <div className="flex justify-center space-x-8 mt-8">
          <Button variant="ghost" className="text-slate-400 hover:text-cyan-400">
            About
          </Button>
          <Button variant="ghost" className="text-slate-400 hover:text-cyan-400">
            For Teachers
          </Button>
        </div>
      </div>
    </div>
  );
};

// Main Physics Lab Component
const PhysicsLab = ({ onBack }) => {
  const [topics, setTopics] = useState({});
  const [selectedTopic, setSelectedTopic] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [currentTask, setCurrentTask] = useState(null);
  const [taskHistory, setTaskHistory] = useState([]);
  const [userAnswer, setUserAnswer] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSolution, setShowSolution] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [generationProgress, setGenerationProgress] = useState(0);

  // Load topics on component mount
  useEffect(() => {
    loadTopics();
    loadHistory();
  }, []);

  const loadTopics = async () => {
    try {
      const response = await axios.get(`${API}/topics`);
      setTopics(response.data);
    } catch (error) {
      toast.error("Failed to load topics");
      console.error(error);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`);
      setTaskHistory(response.data);
    } catch (error) {
      console.error("Failed to load history:", error);
    }
  };

  const generateTask = async () => {
    if (!selectedTopic || !selectedDifficulty) {
      toast.error("Please select topic and difficulty");
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setCurrentTask(null);
    setUserAnswer("");
    setFeedback(null);
    setShowSolution(false);

    // Simulate AI thinking animation
    const progressInterval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 10;
      });
    }, 200);

    try {
      const response = await axios.post(`${API}/generate`, {
        topic: selectedTopic,
        difficulty: selectedDifficulty,
        count: 1
      });

      clearInterval(progressInterval);
      setGenerationProgress(100);
      
      setTimeout(() => {
        setCurrentTask(response.data[0]);
        setIsGenerating(false);
        setGenerationProgress(0);
        loadHistory();
        toast.success("New physics task generated!");
      }, 500);

    } catch (error) {
      clearInterval(progressInterval);
      setIsGenerating(false);
      setGenerationProgress(0);
      toast.error("Failed to generate task");
      console.error(error);
    }
  };

  const checkAnswer = async () => {
    if (!userAnswer || !currentTask) return;

    try {
      const response = await axios.post(`${API}/check`, {
        task_id: currentTask.id,
        user_answer: parseFloat(userAnswer)
      });

      setFeedback(response.data);
      
      if (response.data.correct) {
        toast.success("Correct answer! 🎉");
      } else {
        toast.error("Incorrect answer. Try again!");
      }
      
    } catch (error) {
      toast.error("Failed to check answer");
      console.error(error);
    }
  };

  const toggleSolution = () => {
    setShowSolution(!showSolution);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      <AnimatedBackground />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="border-b border-slate-800/50 backdrop-blur-sm">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button
                  onClick={onBack}
                  variant="ghost"
                  className="text-slate-400 hover:text-cyan-400"
                  data-testid="back-btn"
                >
                  ← Back to Home
                </Button>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                  Physics Task Console
                </h1>
              </div>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-6 py-8">
          <div className="grid lg:grid-cols-4 gap-8">
            {/* Left Sidebar - Controls */}
            <div className="lg:col-span-1 space-y-6">
              <Card className="bg-slate-800/50 border-cyan-400/30 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-cyan-400 flex items-center">
                    ⚙️ Task Settings
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-slate-300">Physics Topic</Label>
                    <Select value={selectedTopic} onValueChange={setSelectedTopic}>
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="topic-selector">
                        <SelectValue placeholder="Select topic" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.keys(topics).map(topic => (
                          <SelectItem key={topic} value={topic}>{topic}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-slate-300">Difficulty Level</Label>
                    <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="difficulty-selector">
                        <SelectValue placeholder="Select difficulty" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">🟢 Easy</SelectItem>
                        <SelectItem value="medium">🟡 Medium</SelectItem>
                        <SelectItem value="hard">🔴 Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={generateTask}
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-cyan-500 to-violet-500 hover:from-cyan-600 hover:to-violet-600"
                    data-testid="generate-btn"
                  >
                    {isGenerating ? "🧠 AI Thinking..." : "Generate New Task"}
                  </Button>

                  {isGenerating && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Generating...</span>
                        <span className="text-cyan-400">{Math.round(generationProgress)}%</span>
                      </div>
                      <Progress value={generationProgress} className="h-2" />
                      <p className="text-xs text-slate-500 text-center">
                        AI is generating your physics task...
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-3 space-y-6">
              {!currentTask && !isGenerating && (
                <Card className="bg-slate-800/50 border-dashed border-slate-600 backdrop-blur-sm">
                  <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="text-6xl mb-4">🧪</div>
                    <h3 className="text-2xl font-semibold text-slate-300 mb-2">Ready to Start Learning?</h3>
                    <p className="text-slate-400">Select a topic and difficulty level, then generate your first physics task.</p>
                  </CardContent>
                </Card>
              )}

              {currentTask && (
                <Card className="bg-slate-800/50 border-cyan-400/30 backdrop-blur-sm">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-cyan-400">Current Task</CardTitle>
                      <div className="flex space-x-2">
                        <Badge variant="outline" className="border-violet-400 text-violet-400">
                          {currentTask.topic}
                        </Badge>
                        <Badge variant="outline" className="border-cyan-400 text-cyan-400">
                          {currentTask.difficulty}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-700">
                      <p className="text-lg text-slate-100 leading-relaxed" data-testid="task-text">
                        {currentTask.task_text}
                      </p>
                    </div>

                    {/* Diagram */}
                    {currentTask.diagram_svg && (
                      <div className="flex justify-center">
                        <div 
                          className="bg-slate-900/50 p-4 rounded-lg border border-slate-700"
                          dangerouslySetInnerHTML={{ __html: currentTask.diagram_svg }}
                        />
                      </div>
                    )}

                    {/* Formula Display */}
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 text-center">
                      <Label className="text-slate-400 text-sm">Formula:</Label>
                      <div className="mt-2 text-xl">
                        <InlineMath math={currentTask.latex.replace(/\\\\/g, '\\')} />
                      </div>
                    </div>

                    <Separator className="bg-slate-700" />

                    {/* Answer Input */}
                    <div className="space-y-4">
                      <Label className="text-slate-300 text-lg">Your Answer:</Label>
                      <div className="flex space-x-4">
                        <Input
                          type="number"
                          value={userAnswer}
                          onChange={(e) => setUserAnswer(e.target.value)}
                          placeholder="Enter numerical answer"
                          className="bg-slate-700/50 border-slate-600 text-white text-lg"
                          data-testid="answer-input"
                        />
                        <span className="flex items-center text-slate-400 text-lg">
                          {currentTask.units}
                        </span>
                        <Button
                          onClick={checkAnswer}
                          disabled={!userAnswer}
                          className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
                          data-testid="check-answer-btn"
                        >
                          Check Answer
                        </Button>
                      </div>
                    </div>

                    {/* Feedback */}
                    {feedback && (
                      <div className={`p-4 rounded-lg border ${
                        feedback.correct 
                          ? 'bg-green-900/30 border-green-500/50' 
                          : 'bg-red-900/30 border-red-500/50'
                      }`}>
                        <p className="font-semibold text-lg" data-testid="feedback-text">
                          {feedback.feedback}
                        </p>
                        {feedback.explanation && (
                          <p className="mt-2 text-slate-300">{feedback.explanation}</p>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex space-x-4">
                      <Button
                        onClick={toggleSolution}
                        variant="outline"
                        className="border-violet-400 text-violet-400 hover:bg-violet-400/10"
                        data-testid="show-solution-btn"
                      >
                        {showSolution ? "Hide Solution" : "Show Solution"}
                      </Button>
                    </div>

                    {/* Solution Steps */}
                    {showSolution && (
                      <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-700">
                        <h4 className="text-lg font-semibold text-violet-400 mb-4">Solution Steps:</h4>
                        <ol className="space-y-2">
                          {currentTask.solution_steps.map((step, index) => (
                            <li key={index} className="text-slate-300">
                              <span className="text-cyan-400 font-semibold">{index + 1}.</span> {step}
                            </li>
                          ))}
                        </ol>
                        <div className="mt-4 p-3 bg-cyan-900/20 rounded border border-cyan-500/30">
                          <p className="text-cyan-300">
                            <strong>Final Answer:</strong> {currentTask.numerical_answer} {currentTask.units}
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Task History */}
              {taskHistory.length > 0 && (
                <Card className="bg-slate-800/50 border-slate-600/30 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="text-slate-300">Recent Tasks</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {taskHistory.slice(0, 5).map((task, index) => (
                        <div key={task.id} className="flex items-center justify-between p-3 bg-slate-900/50 rounded border border-slate-700">
                          <div>
                            <span className="text-sm text-slate-400">{task.topic} - {task.difficulty}</span>
                            <p className="text-slate-300 text-sm truncate max-w-md">
                              {task.task_text.substring(0, 60)}...
                            </p>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {task.numerical_answer} {task.units}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [showLab, setShowLab] = useState(false);

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={
            showLab ? (
              <PhysicsLab onBack={() => setShowLab(false)} />
            ) : (
              <LandingPage onStart={() => setShowLab(true)} />
            )
          } />
        </Routes>
      </BrowserRouter>
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155'
          }
        }}
      />
    </div>
  );
}

export default App;