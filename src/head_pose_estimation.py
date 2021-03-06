'''
This is a sample class for a model. You may choose to use it as-is or make any changes to it.
This has been provided just to give you an idea of how to structure your model class.
'''

import numpy as np
from openvino.inference_engine import IENetwork, IECore
import cv2
import sys
import logging

CPU_EXTENSION = "/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so"

class HeadPoseEstimation:
    '''
    Class for the Head Pose Estimation Model.
    '''
    def __init__(self, model_name, device='CPU', extensions=CPU_EXTENSION):
        '''
        TODO: Use this to set your instance variables.
        '''
        model_weight=model_name+'.bin'
        model_structure=model_name+'.xml'
        self.device=device
        self.cpu_extension=extensions
        self.logger=logging.getLogger(__name__)
    
        try:
            self.model=IENetwork(model_structure,model_weight)
        except Exception as e:
            self.logger.exception("Failed to load model. Kindly put the correct path")
        
    def load_model(self):
        '''
        TODO: You will need to complete this method.
        This method is for loading the model to the device specified by the user.
        If your model requires any Plugins, this is where you can load them.
        '''
        self.core=IECore()

        ### TODO: Check for supported layers ###
        supported_layers = self.core.query_network(network=self.model, device_name=self.device)
        unsupported_layers = [l for l in self.model.layers.keys() if l not in supported_layers]
        if len(unsupported_layers)!=0:
            ### TODO: Add any necessary extensions ###
            if self.cpu_extension and "CPU" in self.device:
                self.core.add_extension(self.cpu_extension, self.device)
            else:
                self.logger.info("Add CPU extension and device type or run layer with original framework")
                exit(1)

        self.net=self.core.load_network(network=self.model,device_name=self.device,num_requests=1)

        self.input_name=next(iter(self.model.inputs))
        self.input_shape=self.model.inputs[self.input_name].shape
        #self.output_name=[i for i in self.model.outputs.keys()]
        self.output_name=next(iter(self.model.outputs))
        self.output_shape=self.model.outputs[self.output_name].shape

        return

    def predict(self, image):
        '''
        TODO: You will need to complete this method.
        This method is meant for running predictions on the input image.
        '''
        self.logger.info("preprocess input and start inference")
        
        p_image = self.preprocess_input(image)
        # sync inference
        self.logger.info("infer result")
        outputs=self.net.infer({self.input_name: p_image})
        self.logger.info("infered result")
        # wait for the result
        
        if self.net.requests[0].wait(-1) == 0:
            # get the output of the inference
            outputs=self.net.requests[0].outputs
            
            return self.preprocess_output(outputs, image)

    def preprocess_input(self, image):
        '''
        Before feeding the data into the model for inference,
        you might have to preprocess it. This function is where you can do that.
        '''
        dsize = (self.input_shape[3], self.input_shape[2])
        image = cv2.resize(image,(dsize))
        image = image.transpose((2,0,1))
        image = image.reshape(1,*image.shape)
        return image

    def preprocess_output(self, outputs, image):
        '''
        Before feeding the output of this model to the next model,
        you might have to preprocess the output. This function is where you can do that.
        '''
        self.logger.info(" Getting the yaw, pitch, and roll angles ")
        angles = []
        
        angles.append(outputs['angle_y_fc'][0][0])
        angles.append(outputs['angle_p_fc'][0][0])
        angles.append(outputs['angle_r_fc'][0][0])
        
        cv2.putText(image, "Estimated yaw:{:.2f} | Estimated pitch:{:.2f}".format(angles[0],angles[1]), (10,20), cv2.FONT_HERSHEY_COMPLEX, 0.25, (0,255,0),1)
        cv2.putText(image, "Estimated roll:{:.2f}".format(angles[2]), (10,30), cv2.FONT_HERSHEY_COMPLEX, 0.25, (0,255,0),1)
        return angles, image
