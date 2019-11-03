#version 450 core

layout (location = 0) in vec4 position;
layout (location = 1) in vec4 color;
layout (location = 2) in vec4 normal;
layout (location = 3) in vec4 texcoord;

layout (location = 0) uniform mat4 proj_matrix;

out VS_OUT {
  vec4 color;
  vec4 normal;
  vec2 texcoord;
} vs_out;


void main() {
  gl_Position = proj_matrix * position;
  vs_out.color = color;
  vs_out.normal = normal;
  vs_out.texcoord = texcoord.xy;
}
