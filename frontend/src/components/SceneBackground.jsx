import { useMemo } from 'react';
import { getScene } from '../utils/sceneConfig';

function RainEffect() {
  const drops = useMemo(() => (
    Array.from({ length: 12 }, (_, i) => ({
      id: i,
      left: `${(i * 8.3) + Math.random() * 5}%`,
      delay: `${Math.random() * 2}s`,
      duration: `${0.6 + Math.random() * 0.4}s`,
      opacity: 0.3 + Math.random() * 0.4,
    }))
  ), []);
  return drops.map((d) => (
    <div key={d.id} className="scene-drop" style={{ left: d.left, animationDelay: d.delay, animationDuration: d.duration, opacity: d.opacity }} />
  ));
}

function StarsEffect() {
  const stars = useMemo(() => (
    Array.from({ length: 8 }, (_, i) => ({
      id: i,
      left: `${10 + Math.random() * 80}%`,
      top: `${5 + Math.random() * 40}%`,
      delay: `${Math.random() * 3}s`,
      size: 2 + Math.random() * 3,
    }))
  ), []);
  return stars.map((s) => (
    <div key={s.id} className="scene-star" style={{ left: s.left, top: s.top, animationDelay: s.delay, width: s.size, height: s.size }} />
  ));
}

function FireEffect() {
  const sparks = useMemo(() => (
    Array.from({ length: 10 }, (_, i) => ({
      id: i,
      left: `${10 + Math.random() * 80}%`,
      delay: `${Math.random() * 2}s`,
      duration: `${1 + Math.random() * 1.5}s`,
      size: 2 + Math.random() * 4,
    }))
  ), []);
  return sparks.map((s) => (
    <div key={s.id} className="scene-spark" style={{ left: s.left, animationDelay: s.delay, animationDuration: s.duration, width: s.size, height: s.size }} />
  ));
}

function FogEffect() {
  const clouds = useMemo(() => (
    Array.from({ length: 3 }, (_, i) => ({
      id: i,
      top: `${20 + i * 25}%`,
      delay: `${i * 2}s`,
      width: 120 + i * 40,
      height: 40 + i * 15,
      opacity: 0.08 + i * 0.03,
    }))
  ), []);
  return clouds.map((c) => (
    <div key={c.id} className="scene-fog" style={{ top: c.top, animationDelay: c.delay, width: c.width, height: c.height, opacity: c.opacity }} />
  ));
}

function LightningEffect() {
  return <div className="scene-lightning" />;
}

function SparkleEffect() {
  const dots = useMemo(() => (
    Array.from({ length: 6 }, (_, i) => ({
      id: i,
      left: `${10 + Math.random() * 80}%`,
      top: `${10 + Math.random() * 50}%`,
      delay: `${Math.random() * 2.5}s`,
      size: 4 + Math.random() * 6,
    }))
  ), []);
  return dots.map((d) => (
    <div key={d.id} className="scene-sparkle" style={{ left: d.left, top: d.top, animationDelay: d.delay, width: d.size, height: d.size }} />
  ));
}

const EFFECTS = {
  rain: RainEffect,
  stars: StarsEffect,
  fire: FireEffect,
  fog: FogEffect,
  lightning: LightningEffect,
  sparkle: SparkleEffect,
};

export default function SceneBackground({ emotion, children }) {
  const scene = useMemo(() => getScene(emotion), [emotion]);
  const EffectComponent = scene.animation ? EFFECTS[scene.animation] : null;

  return (
    <div className="scene-container" style={{ background: scene.gradient }}>
      {EffectComponent && (
        <div className="scene-effects">
          <EffectComponent />
        </div>
      )}
      {children}
    </div>
  );
}
