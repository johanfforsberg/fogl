#version 450 core

layout (binding = 0) uniform sampler2D colorTex;
layout (binding = 1) uniform sampler2D normalTex;

in VS_OUT {
  vec2 texcoord;
} fs_in;

out vec4 color;

void main(void) {
  color = texture(normalTex, fs_in.texcoord);
}
