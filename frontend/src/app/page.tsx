import React from "react";
import { WavyBackground } from "@/components/ui/wavy-background";

export default function Home() {
  return (
    <WavyBackground className="max-w-4xl mx-auto pb-40">
      <p className="text-2xl md:text-4xl lg:text-7xl text-white font-bold inter-var text-center pt-20">
        Resume Parsing Segmentation Model
      </p>
      <p className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center">
        Get the areas of occupied by each section/heading present in the resume in the form of coordinates.
      </p>
      <div className="flex items-center justify-center pt-10">
        <a href="/upload" className="mr-4 px-6 py-3 bg-white hover:bg-cyan-200 text-black font-semibold rounded-md">Get Started</a>
      </div>
    </WavyBackground>
    
  );
}
