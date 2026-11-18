const canvas = document.getElementById("metaball-background");
const gl = canvas.getContext("webgl");

if (!gl) {
    throw new Error("WebGL is not supported!");
}


// Vertex shader
const vertexShaderSource = `
    attribute vec2 position;

    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
    }
`;


// Fragment shader
const fragmentShaderSource = `
    precision mediump float;

    uniform float time;
    uniform vec2 resolution;


    float metaball(vec2 p, vec2 centre, float radius) {

        float d = length(p - centre);

        return (radius * radius) / (d * d + 0.001);
    }


    void main(void) {

        vec2 uv = gl_FragCoord.xy / resolution;

        float t = time;

        vec2 p = uv;

        float field = 0.0;


        field += metaball(p, vec2(
            0.25 + 0.12 * sin(t * 0.5),
            0.35 + 0.10 * cos(t * 0.4)
        ), 0.19);


        field += metaball(p, vec2(
            0.65 + 0.15 * cos(t * 0.4),
            0.65 + 0.12 * sin(t * 0.3)
        ), 0.22);


        field += metaball(p, vec2(
            0.45 + 0.12 * sin(t * 0.3),
            0.50 + 0.15 * cos(t * 0.5)
        ), 0.20);


        field += metaball(p, vec2(
            0.80 + 0.08 * sin(t * 0.6),
            0.20 + 0.12 * cos(t * 0.4)
        ), 0.16);


        field += metaball(p, vec2(
            0.15 + 0.10 * cos(t * 0.3),
            0.75 + 0.08 * sin(t * 0.5)
        ), 0.16);


        field += metaball(p, vec2(
            0.85 + 0.08 * sin(t * 0.4),
            0.55 + 0.10 * cos(t * 0.6)
        ), 0.18);


        field += metaball(p, vec2(
            0.35 + 0.12 * cos(t * 0.6),
            0.15 + 0.08 * sin(t * 0.3)
        ), 0.14);


        field += metaball(p, vec2(
            0.70 + 0.10 * sin(t * 0.5),
            0.85 + 0.06 * cos(t * 0.4)
        ), 0.15);


        vec3 colour = vec3(0.025, 0.015, 0.08);

        float glow = smoothstep(0.7, 2.2, field);


        vec3 blobColour = vec3(
            0.45 + 0.35 * sin(t + uv.x * 3.0),
            0.15 + 0.25 * sin(t * 0.7 + uv.y * 4.0),
            0.85
        );


        colour = mix(colour, blobColour, glow);

        gl_FragColor = vec4(colour, 1.0);
    }
`;


// Compile shader
function createShader(gl, type, source) {

    const shader = gl.createShader(type);

    gl.shaderSource(shader, source);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {

        console.error(gl.getShaderInfoLog(shader));

        gl.deleteShader(shader);

        return null;
    }

    return shader;
}


// Create program
const vertexShader = createShader(
    gl,
    gl.VERTEX_SHADER,
    vertexShaderSource
);

const fragmentShader = createShader(
    gl,
    gl.FRAGMENT_SHADER,
    fragmentShaderSource
);

if (!vertexShader || !fragmentShader) {
    throw new Error("Could not compile metaball shaders");
}

const program = gl.createProgram();

gl.attachShader(program, vertexShader);
gl.attachShader(program, fragmentShader);

gl.linkProgram(program);

if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(gl.getProgramInfoLog(program));
}

gl.useProgram(program);


// Fullscreen quad
const vertices = new Float32Array([
    -1, -1,
     1, -1,
    -1,  1,
     1,  1
]);

const buffer = gl.createBuffer();

gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

const positionLocation = gl.getAttribLocation(
    program,
    "position"
);

gl.enableVertexAttribArray(positionLocation);

gl.vertexAttribPointer(
    positionLocation,
    2,
    gl.FLOAT,
    false,
    0,
    0
);


// Shader uniforms
const timeLocation = gl.getUniformLocation(program, "time");
const resolutionLocation = gl.getUniformLocation(program, "resolution");


// Resize canvas
function resizeCanvas() {

    const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);

    canvas.width = Math.floor(canvas.clientWidth * pixelRatio);
    canvas.height = Math.floor(canvas.clientHeight * pixelRatio);

    gl.viewport(0, 0, canvas.width, canvas.height);
}


// Animation
let startTime = performance.now();

function animate(now) {

    resizeCanvasIfNeeded();

    const time = (now - startTime) / 1000;

    gl.uniform1f(timeLocation, time);

    gl.uniform2f(
        resolutionLocation,
        canvas.width,
        canvas.height
    );

    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    requestAnimationFrame(animate);
}


let previousWidth = 0;
let previousHeight = 0;

function resizeCanvasIfNeeded() {

    if (
        canvas.width !== Math.floor(canvas.clientWidth * Math.min(window.devicePixelRatio || 1, 1.5)) ||
        canvas.height !== Math.floor(canvas.clientHeight * Math.min(window.devicePixelRatio || 1, 1.5))
    ) {
        resizeCanvas();
    }
}


resizeCanvas();

requestAnimationFrame(animate);