import { useState, useEffect, useRef } from 'react';

export function useTypewriterPlaceholder(
  phrases,
  { typingSpeed = 60, deleteSpeed = 40, pauseDuration = 2000, paused = false } = {}
) {
  const [displayText, setDisplayText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const phraseIndex = useRef(0);
  const charIndex = useRef(0);

  useEffect(() => {
    if (paused) return;

    const currentPhrase = phrases[phraseIndex.current];

    const timeout = setTimeout(
      () => {
        if (!isDeleting) {
          charIndex.current += 1;
          setDisplayText(currentPhrase.slice(0, charIndex.current));

          if (charIndex.current === currentPhrase.length) {
            setTimeout(() => setIsDeleting(true), pauseDuration);
          }
        } else {
          charIndex.current -= 1;
          setDisplayText(currentPhrase.slice(0, charIndex.current));

          if (charIndex.current === 0) {
            setIsDeleting(false);
            phraseIndex.current = (phraseIndex.current + 1) % phrases.length;
          }
        }
      },
      isDeleting ? deleteSpeed : typingSpeed
    );

    return () => clearTimeout(timeout);
  }, [displayText, isDeleting, paused, phrases, typingSpeed, deleteSpeed, pauseDuration]);

  return displayText;
}
