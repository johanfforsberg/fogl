#version 450 core

layout (binding=0) uniform sampler2D color;

in VS_OUT {
  // vec3 color;
  vec2 texcoord;
} fs_in;

out vec4 color_out;

void main(void)
{
  vec4 pixel = texture(color, fs_in.texcoord);
  color_out = pixel;
}
