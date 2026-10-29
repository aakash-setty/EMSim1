import * as T from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
globalThis.THREE = Object.assign({}, T, { OrbitControls });
