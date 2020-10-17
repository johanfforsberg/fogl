#version 450 core

layout (location = 0) in vec4 position;
layout (location = 1) in vec4 color;
layout (location = 2) in vec4 normal;
layout (location = 3) in vec4 texcoord;

layout (location = 0) uniform mat4 view_matrix;
layout (location = 1) uniform mat4 model_matrix;

out VS_OUT {
  vec4 color;
  vec3 normal;
  vec4 position;
  vec2 texcoord;
} vs_out;


void main() {
  gl_Position = (view_matrix * model_matrix) * position;
  vs_out.color = color;
  vs_out.normal = transpose(inverse(mat3(model_matrix))) * normal.xyz;
  vs_out.position = model_matrix * position;
  vs_out.texcoord = texcoord.xy;
}
