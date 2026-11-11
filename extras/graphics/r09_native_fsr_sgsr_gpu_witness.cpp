// SPDX-License-Identifier: GPL-3.0-or-later
// REAL pinned-vendor FSR1 EASU + RCAS + SGSR GLSL on Vulkan/Lavapipe.
// Executes the compiled vendor SPIR-V, not the generic spatial fixture.
// Small raster host proof only: not an invocation of the Eden PS5 renderer,
// not a learned neural model, not a real PS5 GPU performance measurement.
//
// Reuse the Khronos-validated host Vulkan image/memory loader in one TU.
// Production shader algorithms remain entirely in vendor GLSL sources.
#define main R09StandaloneSpatialTestMain
#include "r09_composable_vk_spatial_chain.cpp"
#undef main
#include <bit>
#include <limits>

namespace {
struct GraphPass {
    VkFramebuffer framebuffer{};
    VkPipeline pipeline{};
    VkPipelineLayout layout{};
    VkDescriptorSet descriptor{};
    VkExtent2D output{};
};
struct NativeGraph {
    Host& h;
    VkRenderPass renderpass{};
    std::array<VkFramebuffer,3u> framebuffers{};
    ~NativeGraph(){
        if(!h.device)return;
        (void)vkDeviceWaitIdle(h.device);
        for(auto f:framebuffers)if(f)vkDestroyFramebuffer(h.device,f,nullptr);
        if(renderpass)vkDestroyRenderPass(h.device,renderpass,nullptr);
    }
};
std::uint32_t Bits(float f) {return std::bit_cast<std::uint32_t>(f);}
struct FsrConstants {std::uint32_t c[16]{};};
FsrConstants EasuConstants(unsigned w,unsigned h,unsigned outw,unsigned outh){
    // Exact 64-byte upstream FsrEasuConOffset field layout, full crop.
    FsrConstants p{};
    const float iw=float(w),ih=float(h),ow=float(outw),oh=float(outh);
    p.c[0]=Bits(iw/ow);
    p.c[1]=Bits(ih/oh);
    p.c[2]=Bits(0.5f*iw/ow-0.5f);
    p.c[3]=Bits(0.5f*ih/oh-0.5f);
    p.c[4]=Bits(1.f/iw);p.c[5]=Bits(1.f/ih);
    p.c[6]=Bits(1.f/iw);p.c[7]=Bits(-1.f/ih);
    p.c[8]=Bits(-1.f/iw);p.c[9]=Bits(2.f/ih);
    p.c[10]=Bits(1.f/iw);p.c[11]=Bits(2.f/ih);
    p.c[12]=Bits(0.f);p.c[13]=Bits(4.f/ih);
    return p;
}
FsrConstants RcasConstants(){
    // Sharpening slider=0: AMD FsrRcasCon(scale=0) => exp2(0)=1.
    FsrConstants p{};
    p.c[0]=Bits(1.f);
    return p;
}
std::array<std::uint32_t,9u> SgsrConstants(unsigned w,unsigned h,
                                            float sharpness){
    // Exact native SGSR::Draw vertex+fragment float32 push layout.
    return {Bits(1.f/float(w)),Bits(1.f/float(h)),
            Bits(float(w)),Bits(float(h)),
            Bits(1.f),Bits(1.f),Bits(0.f),Bits(0.f),
            Bits(sharpness)};
}
VkRenderPass CreateRenderPass(Host& h){
    VkAttachmentDescription color{};
    color.format=VK_FORMAT_R16G16B16A16_SFLOAT;
    color.samples=VK_SAMPLE_COUNT_1_BIT;
    color.loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR;
    color.storeOp=VK_ATTACHMENT_STORE_OP_STORE;
    color.stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    color.stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE;
    color.initialLayout=VK_IMAGE_LAYOUT_GENERAL;
    color.finalLayout=VK_IMAGE_LAYOUT_GENERAL;
    VkAttachmentReference ref{0u,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
    VkSubpassDescription sub{};
    sub.pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS;
    sub.colorAttachmentCount=1u;
    sub.pColorAttachments=&ref;
    VkSubpassDependency dependencies[2]{};
    dependencies[0].srcSubpass=VK_SUBPASS_EXTERNAL;
    dependencies[0].dstSubpass=0u;
    dependencies[0].srcStageMask=VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    dependencies[0].dstStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dependencies[0].srcAccessMask=VK_ACCESS_SHADER_READ_BIT;
    dependencies[0].dstAccessMask=VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    dependencies[1].srcSubpass=0u;
    dependencies[1].dstSubpass=VK_SUBPASS_EXTERNAL;
    dependencies[1].srcStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dependencies[1].dstStageMask=VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT|
                                 VK_PIPELINE_STAGE_TRANSFER_BIT;
    dependencies[1].srcAccessMask=VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    dependencies[1].dstAccessMask=VK_ACCESS_SHADER_READ_BIT|
                                  VK_ACCESS_TRANSFER_READ_BIT;
    VkRenderPassCreateInfo ci{};
    ci.sType=VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount=1u;ci.pAttachments=&color;
    ci.subpassCount=1u;ci.pSubpasses=&sub;
    ci.dependencyCount=2u;ci.pDependencies=dependencies;
    VkRenderPass pass{};
    Check(vkCreateRenderPass(h.device,&ci,nullptr,&pass),"native renderpass");
    return pass;
}
VkPipeline MakeGraphicsPipeline(Host& h,VkRenderPass rp,
                                VkShaderModule vs,VkShaderModule fs,
                                VkPipelineLayout layout,
                                VkExtent2D extent){
    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0].sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage=VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module=vs;stages[0].pName="main";
    stages[1].sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage=VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module=fs;stages[1].pName="main";
    VkPipelineVertexInputStateCreateInfo input{};
    input.sType=VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType=VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkViewport viewport{0.f,0.f,float(extent.width),float(extent.height),0.f,1.f};
    VkRect2D scissor{{0,0},extent};
    VkPipelineViewportStateCreateInfo vp{};
    vp.sType=VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount=1u;vp.pViewports=&viewport;
    vp.scissorCount=1u;vp.pScissors=&scissor;
    VkPipelineRasterizationStateCreateInfo raster{};
    raster.sType=VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    raster.polygonMode=VK_POLYGON_MODE_FILL;
    raster.cullMode=VK_CULL_MODE_NONE;
    raster.frontFace=VK_FRONT_FACE_COUNTER_CLOCKWISE;
    raster.lineWidth=1.f;
    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType=VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState attachment{};
    attachment.colorWriteMask=VK_COLOR_COMPONENT_R_BIT|
        VK_COLOR_COMPONENT_G_BIT|VK_COLOR_COMPONENT_B_BIT|
        VK_COLOR_COMPONENT_A_BIT;
    VkPipelineColorBlendStateCreateInfo blend{};
    blend.sType=VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend.attachmentCount=1u;blend.pAttachments=&attachment;
    VkGraphicsPipelineCreateInfo ci{};
    ci.sType=VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    ci.stageCount=2u;ci.pStages=stages;
    ci.pVertexInputState=&input;ci.pInputAssemblyState=&ia;
    ci.pViewportState=&vp;ci.pRasterizationState=&raster;
    ci.pMultisampleState=&ms;ci.pColorBlendState=&blend;
    ci.layout=layout;ci.renderPass=rp;
    VkPipeline result{};
    Check(vkCreateGraphicsPipelines(h.device,VK_NULL_HANDLE,1u,
        &ci,nullptr,&result),"native FSR/SGSR pipeline");
    h.pipelines.push_back(result);
    return result;
}
float HalfToFloat(std::uint16_t v){
    const unsigned exponent=(v>>10u)&31u;
    const unsigned mantissa=v&1023u;
    const float sign=(v&0x8000u)?-1.f:1.f;
    if(exponent==31u)return mantissa?
        std::numeric_limits<float>::quiet_NaN():
        sign*std::numeric_limits<float>::infinity();
    if(exponent==0u)return sign*std::ldexp(float(mantissa),-24);
    return sign*std::ldexp(float(mantissa+1024u),int(exponent)-25);
}
void RunNative(Host& h,const std::array<const char*,5u>& shaders,
               bool edge,bool gradient){
    // 1280×720->1440p->4K needs real PS5 qualification; use smaller
    // but exact ratio on software Vulkan for non-toy shader correctness.
    constexpr VkExtent2D source{128u,72u};
    constexpr VkExtent2D intermediate{256u,144u};
    constexpr VkExtent2D final{512u,288u};
    VkQueueFamilyProperties qp{};
    std::uint32_t count{};
    vkGetPhysicalDeviceQueueFamilyProperties(h.physical,&count,nullptr);
    std::vector<VkQueueFamilyProperties> queues(count);
    vkGetPhysicalDeviceQueueFamilyProperties(h.physical,&count,queues.data());
    if(!(queues.at(h.family).queueFlags&VK_QUEUE_GRAPHICS_BIT))
        throw std::runtime_error("No Vulkan graphics queue in host fixture");

    NativeGraph graph{h};
    graph.renderpass=CreateRenderPass(h);
    std::array<Image,4u> images{};
    images[0]=h.NewImage(source.width,source.height,
        VK_FORMAT_R32G32B32A32_SFLOAT,
        VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT);
    for(unsigned i=1;i<4u;++i){
        const auto e=i==3u?final:intermediate;
        images[i]=h.NewImage(e.width,e.height,
            VK_FORMAT_R16G16B16A16_SFLOAT,
            VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|
            VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
        VkFramebufferCreateInfo fb{};
        fb.sType=VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fb.renderPass=graph.renderpass;
        fb.attachmentCount=1u;fb.pAttachments=&images[i].view;
        fb.width=e.width;fb.height=e.height;fb.layers=1u;
        Check(vkCreateFramebuffer(h.device,&fb,nullptr,
             &graph.framebuffers[i-1u]),"native framebuffer");
    }
    const std::size_t floats=std::size_t(source.width)*source.height*4u;
    std::vector<float> input(floats);
    for(unsigned y=0;y<source.height;++y)
      for(unsigned x=0;x<source.width;++x){
        const auto base=(std::size_t(y)*source.width+x)*4u;
        // Uniform primary oracle + optional nonuniform edge-pattern fixture.
        input[base]=gradient?0.2f+(x>=64u?0.36f:0.f)+
                             float(x)*0.0013f:0.3f;
        input[base+1u]=gradient?0.2f+float(y)*0.004f:0.45f;
        input[base+2u]=gradient?0.25f+float(x+y)*0.0015f:0.6f;
        input[base+3u]=1.f;
    }
    const auto upload=h.NewBuffer(input.size()*sizeof(float),
                                  VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    void* mapped{};
    Check(vkMapMemory(h.device,upload.memory,0u,upload.bytes,
        0u,&mapped),"input map");
    std::memcpy(mapped,input.data(),std::size_t(upload.bytes));
    vkUnmapMemory(h.device,upload.memory);
    std::array<Buffer,3u> readbacks{};
    for(unsigned i=0;i<3u;++i){
        const auto e=i==2u?final:intermediate;
        readbacks[i]=h.NewBuffer(VkDeviceSize(e.width)*e.height*8u,
                                 VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    }
    VkSamplerCreateInfo sam{};
    sam.sType=VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sam.magFilter=VK_FILTER_LINEAR;
    sam.minFilter=VK_FILTER_LINEAR;
    sam.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sam.addressModeU=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sam.addressModeV=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sam.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    Check(vkCreateSampler(h.device,&sam,nullptr,&h.sampler),
          "native image sampler");
    VkDescriptorSetLayoutBinding binding{};
    binding.binding=0u;
    binding.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    binding.descriptorCount=1u;binding.stageFlags=VK_SHADER_STAGE_FRAGMENT_BIT;
    const auto set_layout=h.SetLayout(&binding,1u);
    VkDescriptorPoolSize pool_size{
        VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,3u};
    VkDescriptorPoolCreateInfo pci{};
    pci.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pci.maxSets=3u;pci.poolSizeCount=1u;pci.pPoolSizes=&pool_size;
    Check(vkCreateDescriptorPool(h.device,&pci,nullptr,&h.descriptor_pool),
          "native descriptor pool");
    std::array<VkDescriptorSetLayout,3u> layouts{
        set_layout,set_layout,set_layout};
    std::array<VkDescriptorSet,3u> sets{};
    VkDescriptorSetAllocateInfo ai{};
    ai.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ai.descriptorPool=h.descriptor_pool;
    ai.descriptorSetCount=3u;ai.pSetLayouts=layouts.data();
    Check(vkAllocateDescriptorSets(h.device,&ai,sets.data()),
          "native descriptor sets");
    std::array<VkDescriptorImageInfo,3u> infos{};
    std::array<VkWriteDescriptorSet,3u> writes{};
    for(unsigned i=0;i<3u;++i){
        infos[i]={h.sampler,images[i].view,VK_IMAGE_LAYOUT_GENERAL};
        writes[i].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[i].dstSet=sets[i];writes[i].dstBinding=0u;
        writes[i].descriptorCount=1u;
        writes[i].descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        writes[i].pImageInfo=&infos[i];
    }
    vkUpdateDescriptorSets(h.device,3u,writes.data(),0u,nullptr);

    std::array<VkShaderModule,5u> modules{};
    for(unsigned i=0;i<shaders.size();++i)
        modules[i]=h.Shader(shaders[i]);
    std::array<VkPipelineLayout,2u> pls{};
    for(unsigned i=0;i<2u;++i){
        const VkPushConstantRange push{
            i==0u?VK_SHADER_STAGE_FRAGMENT_BIT:
                VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,
            0u,i==0u?64u:36u};
        VkPipelineLayoutCreateInfo li{};
        li.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        li.setLayoutCount=1u;li.pSetLayouts=&set_layout;
        li.pushConstantRangeCount=1u;li.pPushConstantRanges=&push;
        Check(vkCreatePipelineLayout(h.device,&li,nullptr,&pls[i]),
              "native graphics pipeline layout");
        h.pipeline_layouts.push_back(pls[i]);
    }
    std::array<GraphPass,3u> passes{};
    passes[0]={graph.framebuffers[0],
        MakeGraphicsPipeline(h,graph.renderpass,modules[0],modules[1],
                             pls[0],intermediate),
        pls[0],sets[0],intermediate};
    passes[1]={graph.framebuffers[1],
        MakeGraphicsPipeline(h,graph.renderpass,modules[0],modules[2],
                             pls[0],intermediate),
        pls[0],sets[1],intermediate};
    passes[2]={graph.framebuffers[2],
        MakeGraphicsPipeline(h,graph.renderpass,modules[3],modules[4],
                             pls[1],final),
        pls[1],sets[2],final};
    const auto easu=EasuConstants(source.width,source.height,
                                   intermediate.width,intermediate.height);
    const auto rcas=RcasConstants();
    const auto sgsr=SgsrConstants(intermediate.width,
                                  intermediate.height,1.5f);

    VkCommandBufferBeginInfo bi{};
    bi.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    Check(vkBeginCommandBuffer(h.cmd,&bi),"begin native 3-pass cmd");
    ImageBarrier(h.cmd,Transition(images[0].image,
        VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        0u,VK_ACCESS_TRANSFER_WRITE_BIT),
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkBufferImageCopy region{};
    region.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u};
    region.imageExtent={source.width,source.height,1u};
    vkCmdCopyBufferToImage(h.cmd,upload.buffer,images[0].image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1u,&region);
    ImageBarrier(h.cmd,Transition(images[0].image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,
        VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT),
        VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
    for(unsigned i=0;i<3u;++i){
        const auto& pass=passes[i];
        ImageBarrier(h.cmd,Transition(images[i+1u].image,
            VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL,
            0u,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT),
            VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
        VkClearValue clear{};
        clear.color.float32[0]=0.03125f;
        clear.color.float32[1]=0.03125f;
        clear.color.float32[2]=0.03125f;
        clear.color.float32[3]=1.f;
        VkRenderPassBeginInfo ri{};
        ri.sType=VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
        ri.renderPass=graph.renderpass;
        ri.framebuffer=pass.framebuffer;
        ri.renderArea={{0,0},pass.output};
        ri.clearValueCount=1u;ri.pClearValues=&clear;
        vkCmdBeginRenderPass(h.cmd,&ri,VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(h.cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,
                          pass.pipeline);
        vkCmdBindDescriptorSets(h.cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,
            pass.layout,0u,1u,&pass.descriptor,0u,nullptr);
        if(i==0u)vkCmdPushConstants(h.cmd,pass.layout,
             VK_SHADER_STAGE_FRAGMENT_BIT,0u,64u,&easu);
        else if(i==1u)vkCmdPushConstants(h.cmd,pass.layout,
             VK_SHADER_STAGE_FRAGMENT_BIT,0u,64u,&rcas);
        else vkCmdPushConstants(h.cmd,pass.layout,
             VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,
             0u,36u,sgsr.data());
        vkCmdDraw(h.cmd,3u,1u,0u,0u);
        vkCmdEndRenderPass(h.cmd);
        // Real color-attachment writes from EASU/RCAS/SGSR must be
        // visible to NEXT shader's sampler and to verification readback.
        ImageBarrier(h.cmd,Transition(images[i+1u].image,
            VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_GENERAL,
            VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_TRANSFER_READ_BIT),
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT|
            VK_PIPELINE_STAGE_TRANSFER_BIT);
        VkBufferImageCopy output_copy{};
        output_copy.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0u,0u,1u};
        output_copy.imageExtent={pass.output.width,pass.output.height,1u};
        vkCmdCopyImageToBuffer(h.cmd,images[i+1u].image,
            VK_IMAGE_LAYOUT_GENERAL,readbacks[i].buffer,1u,&output_copy);
    }
    VkMemoryBarrier to_host{};
    to_host.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    to_host.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
    to_host.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(h.cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_HOST_BIT,0u,1u,&to_host,
        0u,nullptr,0u,nullptr);
    Check(vkEndCommandBuffer(h.cmd),"end native graph");
    VkFence fence{};
    VkFenceCreateInfo fi{};
    fi.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    Check(vkCreateFence(h.device,&fi,nullptr,&fence),"native fence");
    VkSubmitInfo submit{};
    submit.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit.commandBufferCount=1u;submit.pCommandBuffers=&h.cmd;
    Check(vkQueueSubmit(h.queue,1u,&submit,fence),"submit native shaders");
    Check(vkWaitForFences(h.device,1u,&fence,VK_TRUE,20'000'000'000ull),
          "wait native GPU readback fence");
    vkDestroyFence(h.device,fence,nullptr);
    if(h.validation_errors!=0u)
        throw std::runtime_error("Khronos reported native GPU pipeline hazards");
    std::array<float,3u> maxDelta{};
    for(unsigned i=0;i<3u;++i){
        const auto extent=i==2u?final:intermediate;
        const auto& b=readbacks[i];
        void* ptr{};
        Check(vkMapMemory(h.device,b.memory,0u,b.bytes,0u,&ptr),
              "map real native shader output");
        const auto* half=static_cast<const std::uint16_t*>(ptr);
        float minr=100.f,maxr=-100.f;
        for(std::size_t pixel=0u;
            pixel<std::size_t(extent.width)*extent.height;++pixel){
            for(unsigned c=0;c<4u;++c){
                const float value=HalfToFloat(half[pixel*4u+c]);
                if(!std::isfinite(value)){
                    vkUnmapMemory(h.device,b.memory);
                    throw std::runtime_error("Nonfinite authentic FSR/SGSR pixel");
                }
                if(c==0u){minr=std::min(minr,value);maxr=std::max(maxr,value);}
                if(!gradient && c<3u){
                    const float expected=c==0u?0.3f:c==1u?0.45f:0.6f;
                    maxDelta[i]=std::max(maxDelta[i],std::fabs(value-expected));
                    if(std::fabs(value-expected)>0.12f){
                        vkUnmapMemory(h.device,b.memory);
                        throw std::runtime_error(
                            "Authentic native shaders fail constant RGB oracle "
                            "stage="+std::to_string(i)+
                            " value="+std::to_string(value)+
                            " expected="+std::to_string(expected));
                    }
                }
                if(c==3u&&std::fabs(value-1.f)>0.04f){
                    vkUnmapMemory(h.device,b.memory);
                    throw std::runtime_error("Native RGBA output alpha wrong");
                }
            }
        }
        if(gradient&&(minr>=0.34f||maxr<=0.43f)){
            vkUnmapMemory(h.device,b.memory);
            throw std::runtime_error(
                "Gradient failed to propagate to native stage="+
                std::to_string(i));
        }
        vkUnmapMemory(h.device,b.memory);
        std::cout<<"R09_AUTHENTIC_FSR_SGSR_GPU_STAGE_PASS stage="<<i
                 <<" width="<<extent.width<<" height="<<extent.height
                 <<" red_min="<<minr<<" red_max="<<maxr
                 <<" constant_rgb_max_delta="<<maxDelta[i]<<"\n";
    }
    std::cout<<"R09_AUTHENTIC_FSR1_EASU_RCAS_SGSR_GRAPHICS_GPU_PASS "
             <<"edge="<<edge<<" gradient="<<gradient
             <<" actual_vendor_spirv=YES Khronos_errors=0"
                " PS5=NO learned_neural=NO native_C++_owners=NO\n";
}
} // namespace

int main(int argc,char** argv){
    if(argc!=8){
        std::cerr<<"Usage: native_witness <fsr.vert.spv> <easu.frag.spv> "
            "<rcas.frag.spv> <sgsr.vert.spv> <sgsr.frag.spv> "
            "<normal|edge> <constant|gradient>\n";
        return 2;
    }
    const std::string edge_arg=argv[6],data_arg=argv[7];
    if((edge_arg!="normal"&&edge_arg!="edge")||
       (data_arg!="constant"&&data_arg!="gradient"))return 2;
    try {
        Host h;
        h.Init();
        RunNative(h,{argv[1],argv[2],argv[3],argv[4],argv[5]},
                  edge_arg=="edge",data_arg=="gradient");
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"R09_NATIVE_VENDOR_SHADER_GPU_FAIL "<<e.what()<<"\n";
        return 1;
    }
}
