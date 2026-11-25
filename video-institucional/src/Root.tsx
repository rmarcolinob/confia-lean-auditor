import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
export const Root:React.FC=()=> <Composition id="ConfIA" component={Film} width={1920} height={1080} fps={30} durationInFrames={5400} defaultProps={{captions:true,audio:true}}/>;
