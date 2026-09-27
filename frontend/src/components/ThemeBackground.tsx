import React, { useEffect, useRef } from "react";
import { useTheme } from "../context/ThemeContext";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  baseAlpha: number;
  color: string;
  pulseSpeed?: number;
  pulseVal?: number;
}

const ThemeBackground: React.FC = () => {
  const { theme, currentThemeMeta, isDark } = useTheme();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);

    // Color configurations based on theme
    const primary = currentThemeMeta.primaryColor;
    const secondary = currentThemeMeta.secondaryColor;
    const accent = currentThemeMeta.accentColor;

    // Determine particle parameters per theme
    let particleCount = 42;
    let maxDistance = 110;
    let speedMult = 0.5;

    if (theme === "cyber-space" || theme === "crimson-cyber") {
      particleCount = 55;
      maxDistance = 120;
      speedMult = 0.6;
    } else if (theme === "digital-galaxy") {
      particleCount = 75; // More star particles
      maxDistance = 85;
      speedMult = 0.35;
    } else if (!isDark) {
      particleCount = 34; // Subtle for light themes
      maxDistance = 100;
      speedMult = 0.3;
    }

    const particles: Particle[] = [];
    const colors = [primary, secondary, accent];

    for (let i = 0; i < particleCount; i++) {
      const col = colors[i % colors.length];
      const isStar = theme === "digital-galaxy" && i % 3 === 0;
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * speedMult,
        vy: (Math.random() - 0.5) * speedMult,
        radius: isStar ? Math.random() * 1.5 + 0.8 : Math.random() * 2 + 1,
        baseAlpha: isDark ? (Math.random() * 0.45 + 0.25) : (Math.random() * 0.25 + 0.12),
        color: col,
        pulseSpeed: Math.random() * 0.03 + 0.01,
        pulseVal: Math.random() * Math.PI
      });
    }

    let tick = 0;

    const render = () => {
      tick++;
      ctx.clearRect(0, 0, width, height);

      // 1. Draw theme-specific ambient backdrops
      if (theme === "cyber-space" || theme === "crimson-cyber") {
        // Draw subtle digital cyber grid
        const gridSize = 48;
        ctx.lineWidth = 0.4;
        ctx.strokeStyle = theme === "cyber-space"
          ? "rgba(6, 182, 212, 0.035)"
          : "rgba(244, 63, 94, 0.035)";

        ctx.beginPath();
        for (let x = 0; x < width; x += gridSize) {
          ctx.moveTo(x, 0);
          ctx.lineTo(x, height);
        }
        for (let y = 0; y < height; y += gridSize) {
          ctx.moveTo(0, y);
          ctx.lineTo(width, y);
        }
        ctx.stroke();
      } else if (theme === "mint-technology") {
        // Subtle geometric dot matrix
        const dotGap = 40;
        ctx.fillStyle = "rgba(5, 150, 105, 0.05)";
        for (let x = 20; x < width; x += dotGap) {
          for (let y = 20; y < height; y += dotGap) {
            ctx.fillRect(x, y, 1.2, 1.2);
          }
        }
      }

      // 2. Update and draw particles
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        if (p.pulseVal !== undefined && p.pulseSpeed) {
          p.pulseVal += p.pulseSpeed;
        }

        const currentAlpha = p.pulseVal !== undefined
          ? p.baseAlpha * (0.7 + 0.3 * Math.sin(p.pulseVal))
          : p.baseAlpha;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = currentAlpha;
        ctx.fill();

        // 3. Connect particles with neural lines
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDistance) {
            const lineAlpha = (1 - dist / maxDistance) * (isDark ? 0.16 : 0.08);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = p.color;
            ctx.globalAlpha = lineAlpha;
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 1.0;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [theme, currentThemeMeta, isDark]);

  return (
    <div className={`theme-background-layer theme-${theme}`} aria-hidden="true">
      {/* Dynamic ambient glowing orbs in corners */}
      <div
        className="ambient-orb ambient-orb-1"
        style={{
          background: `radial-gradient(circle, ${currentThemeMeta.primaryColor}24 0%, transparent 68%)`
        }}
      />
      <div
        className="ambient-orb ambient-orb-2"
        style={{
          background: `radial-gradient(circle, ${currentThemeMeta.secondaryColor}1e 0%, transparent 65%)`
        }}
      />
      <div
        className="ambient-orb ambient-orb-3"
        style={{
          background: `radial-gradient(circle, ${currentThemeMeta.accentColor}18 0%, transparent 60%)`
        }}
      />

      {/* Interactive particle & neural network canvas */}
      <canvas ref={canvasRef} className="theme-particles-canvas" />
    </div>
  );
};

export default ThemeBackground;
