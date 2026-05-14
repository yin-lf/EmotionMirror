import { useState } from 'react';
import TopNav from './components/TopNav';
import Sidebar from './components/Sidebar';
import StepInput from './components/StepInput';
import StepAvatar from './components/StepAvatar';
import StepAnalysis from './components/StepAnalysis';
import StepDigitalTwin from './components/StepDigitalTwin';
import './App.css';

const STEPS = [
  { key: 'input',   title: '情绪输入',   desc: '选择模态并输入内容' },
  { key: 'avatar',  title: '数字形象',   desc: '上传分身基础形象' },
  { key: 'analysis', title: '情绪分析',  desc: '查看分析结果' },
  { key: 'twin',    title: '数字分身',   desc: '生成情绪化数字分身' },
];

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState([]);
  const [result, setResult] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);

  const goTo = (step) => {
    setCurrentStep(step);
  };

  const completeAndGo = (nextStep) => {
    if (!completed.includes(currentStep)) {
      setCompleted((prev) => [...prev, currentStep]);
    }
    setCurrentStep(nextStep);
  };

  const goPrev = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <StepInput
            onResult={setResult}
            onNext={() => completeAndGo(1)}
          />
        );
      case 1:
        return (
          <StepAvatar
            onAvatarSelect={setAvatarUrl}
            onAvatarFile={setAvatarFile}
            onNext={() => completeAndGo(2)}
            onPrev={goPrev}
          />
        );
      case 2:
        return (
          <StepAnalysis
            result={result}
            onNext={() => completeAndGo(3)}
            onPrev={goPrev}
          />
        );
      case 3:
        return (
          <StepDigitalTwin
            result={result}
            avatarUrl={avatarUrl}
            avatarFile={avatarFile}
            onPrev={goPrev}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <TopNav />
      <div className="app-body">
        <Sidebar
          steps={STEPS}
          current={currentStep}
          completed={completed}
          onChange={goTo}
        />
        <main className="main-content">
          {renderStep()}
        </main>
      </div>
    </div>
  );
}

export default App;
