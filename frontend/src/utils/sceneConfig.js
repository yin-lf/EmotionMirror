export function getTimePeriod() {
  const h = new Date().getHours();
  if (h >= 6 && h < 12) return 'morning';
  if (h >= 12 && h < 18) return 'afternoon';
  if (h >= 18 && h < 21) return 'evening';
  return 'night';
}

const SCENES = {
  morning: {
    '开心':   { gradient: 'linear-gradient(135deg, #FF9A56 0%, #FF6B95 50%, #FFC3A0 100%)', animation: 'sparkle' },
    '悲伤':   { gradient: 'linear-gradient(135deg, #8E9EAB 0%, #6B7B8D 50%, #556270 100%)', animation: 'rain' },
    '愤怒':   { gradient: 'linear-gradient(135deg, #8B0000 0%, #CC3333 50%, #993333 100%)', animation: 'fire' },
    '焦虑':   { gradient: 'linear-gradient(135deg, #B0BEC5 0%, #CFD8DC 50%, #90A4AE 100%)', animation: 'fog' },
    '恐惧':   { gradient: 'linear-gradient(135deg, #5C2018 0%, #8E9EAB 100%)', animation: 'lightning' },
    '平静':   { gradient: 'linear-gradient(135deg, #FFDEE9 0%, #FFFFFF 100%)', animation: null },
    '厌恶':   { gradient: 'linear-gradient(135deg, #8D9E88 0%, #9EA9A0 100%)', animation: null },
    '惊讶':   { gradient: 'linear-gradient(135deg, #F7DC6F 0%, #F09819 100%)', animation: 'sparkle' },
  },
  afternoon: {
    '开心':   { gradient: 'linear-gradient(135deg, #74B9FF 0%, #FFFFFF 50%, #A8E6CF 100%)', animation: 'sparkle' },
    '悲伤':   { gradient: 'linear-gradient(135deg, #94A3B8 0%, #A0AEC0 50%, #718096 100%)', animation: 'rain' },
    '愤怒':   { gradient: 'linear-gradient(135deg, #E53E3E 0%, #F56565 50%, #ED8936 100%)', animation: 'fire' },
    '焦虑':   { gradient: 'linear-gradient(135deg, #A0AEC0 0%, #718096 100%)', animation: 'fog' },
    '恐惧':   { gradient: 'linear-gradient(135deg, #4A5568 0%, #718096 100%)', animation: 'lightning' },
    '平静':   { gradient: 'linear-gradient(135deg, #D4F1F9 0%, #FFFFFF 100%)', animation: null },
    '厌恶':   { gradient: 'linear-gradient(135deg, #6B8F71 0%, #8FA98F 100%)', animation: null },
    '惊讶':   { gradient: 'linear-gradient(135deg, #FFFFFF 0%, #BEE3F8 100%)', animation: 'sparkle' },
  },
  evening: {
    '开心':   { gradient: 'linear-gradient(135deg, #F093FB 0%, #F5576C 30%, #FFB347 100%)', animation: 'sparkle' },
    '悲伤':   { gradient: 'linear-gradient(135deg, #8B6914 0%, #614385 100%)', animation: 'rain' },
    '愤怒':   { gradient: 'linear-gradient(135deg, #8B0000 0%, #4A0E4E 100%)', animation: 'fire' },
    '焦虑':   { gradient: 'linear-gradient(135deg, #4A5568 0%, #6B46C1 100%)', animation: 'fog' },
    '恐惧':   { gradient: 'linear-gradient(135deg, #553C7B 0%, #4A5568 100%)', animation: 'lightning' },
    '平静':   { gradient: 'linear-gradient(135deg, #FFECD2 0%, #FCB69F 100%)', animation: null },
    '厌恶':   { gradient: 'linear-gradient(135deg, #BDB76B 0%, #8B7D6B 100%)', animation: null },
    '惊讶':   { gradient: 'linear-gradient(135deg, #A855F7 0%, #F97316 100%)', animation: 'sparkle' },
  },
  night: {
    '开心':   { gradient: 'linear-gradient(135deg, #0F2027 0%, #203A43 40%, #2C5364 100%)', animation: 'stars' },
    '悲伤':   { gradient: 'linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)', animation: 'rain' },
    '愤怒':   { gradient: 'linear-gradient(135deg, #1A0000 0%, #4A0000 50%, #1A0000 100%)', animation: 'fire' },
    '焦虑':   { gradient: 'linear-gradient(135deg, #2D2D2D 0%, #1A1A2E 100%)', animation: 'fog' },
    '恐惧':   { gradient: 'linear-gradient(135deg, #0D0D0D 0%, #1A0033 100%)', animation: 'lightning' },
    '平静':   { gradient: 'linear-gradient(135deg, #0F2027 0%, #2C5364 50%, #203A43 100%)', animation: 'stars' },
    '厌恶':   { gradient: 'linear-gradient(135deg, #1A2F1A 0%, #0D1B0D 100%)', animation: null },
    '惊讶':   { gradient: 'linear-gradient(135deg, #1E3A5F 0%, #4A0E4E 100%)', animation: 'sparkle' },
  },
};

export function getScene(emotion) {
  const period = getTimePeriod();
  return SCENES[period]?.[emotion] || SCENES[period]?.['平静'] || { gradient: 'linear-gradient(135deg, #f9fafb, #ffffff)', animation: null };
}
