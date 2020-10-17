#version 450 core

layout (binding = 3) uniform sampler2D colorTex;

layout (location = 2) uniform vec4 color = vec4(1, 0.5, 0, 1);

in VS_OUT {
  vec4 color;
  vec3 normal;
  vec4 position;
  vec2 texcoord;
} fs_in;


layout (location = 0) out vec4 color_out;
layout (location = 1) out vec4 normal_out;
layout (location = 2) out vec4 position_out;


void main(void) {
  color_out = fs_in.color * color * texture(colorTex, fs_in.texcoord);
  normal_out = vec4(fs_in.normal, 1);
  position_out = fs_in.position;
}
