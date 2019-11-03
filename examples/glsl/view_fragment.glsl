#version 450 core

layout (binding = 3) uniform sampler2D colorTex;
layout (location = 1) uniform vec4 color = vec4(1, 0.5, 0, 1);

in VS_OUT {
  vec4 color;
  vec4 normal;
  vec2 texcoord;
} fs_in;


layout (location = 0) out vec4 color_out;
layout (location = 1) out vec4 normal_out;


void main(void) {
  color_out = fs_in.color * color * texture(colorTex, fs_in.texcoord);
  normal_out = fs_in.normal;
}
