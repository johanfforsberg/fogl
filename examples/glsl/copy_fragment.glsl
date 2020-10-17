#version 450 core

layout (binding = 0) uniform sampler2D colorTex;
layout (binding = 1) uniform sampler2D normalTex;
layout (binding = 2) uniform sampler2D positionTex;
layout (binding = 3) uniform sampler2D shadowDepthTex;

layout (location = 0) uniform vec3 light_position;
layout (location = 1) uniform mat4 shadow_view_matrix;

in VS_OUT {
  vec2 texcoord;
} fs_in;

out vec4 color;


float calculateLighting(vec3 lightPos, vec4 fragPos, vec4 normal) {
  float incidence = clamp(dot(normalize(lightPos - fragPos.xyz), normal.xyz), 0, 1);
  return pow(incidence, 2);
}


float calculateShadow(vec4 lightSpacePosition, float bias) {
  vec3 pos = lightSpacePosition.xyz / lightSpacePosition.w;  // Normalize to {-1, 1}
  pos = pos * 0.5 + 0.5;  // To "texture space"
  float shadowDepth = texture(shadowDepthTex, pos.xy).r;
  float shadow = pos.z - bias > shadowDepth ? 0 : 1;
  return shadow;
}

void main(void) {
  vec4 position = texture(positionTex, fs_in.texcoord);
  vec4 lightSpacePosition = shadow_view_matrix * position;
  float shadow = calculateShadow(lightSpacePosition, 0.03);
  float lighting = calculateLighting(light_position, position,
                                     texture(normalTex, fs_in.texcoord));
  color = shadow * lighting * texture(colorTex, fs_in.texcoord);
}
