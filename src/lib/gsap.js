import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register plugins
gsap.registerPlugin(ScrollTrigger);

// Optional: Set global defaults
gsap.defaults({
  ease: 'power2.out',
  duration: 0.8
});

export { gsap, ScrollTrigger };
export default gsap;
