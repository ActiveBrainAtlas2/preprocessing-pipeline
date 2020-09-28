#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
#uicontrol float gamma slider(min=0.05, max=2.5, default=1, step=0.05)
#uicontrol float linlog slider(min=0, max=1, default=0, step=1)

  void main() {
    float limit = 45000.0;
    float pix = float(toRaw(getDataValue()));

    if (linlog==1.0) {
    	pix = log(pix);
      	limit = 10.0;
    } else {
    pix = pow(pix,gamma);
    limit = 40000.0;
    }


    float pix_val = pix/limit;
  	if(pix_val < min){
  		pix_val = 0.0;
  	}
  	if(pix_val > max){
    	pix_val = 1.0;
  	}


  	if(invert==1.0){
  	  emitGrayscale((1.0 -( pix_val  - brightness)) * exp(contrast)) ;
  	}
  	else{
    	emitGrayscale((pix_val + brightness) *
                  exp(contrast));
  	}

}
// for color
#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
void main() {
  float pix_val = toNormalized(getDataValue());
  if(pix_val < min){
  	pix_val = 0.0;
  }
  if(pix_val > max){
    pix_val = 1.0;
  }

  if(invert==1.0){

  	  emitRGB(vec3((1.0 -(pix_val - brightness)) *
       exp(contrast),0,0));
  }
  else{
    emitRGB(vec3((pix_val + brightness) *
                  exp(contrast),0,0));
  }

}


# for 1st channel with the other ones color 16bit
#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
void main() {
    float limit = 40000.0;
    float pix_val = float(toRaw(getDataValue()));
  if(pix_val < min){
  	pix_val = 0.0;
  }
  if(pix_val > max){
    pix_val = 1.0;
  }

  if(invert==1.0){
  	  emitGrayscale((1.0 -(pix_val - brightness)) *
       exp(contrast));
  }
  else{
    emitGrayscale((pix_val + brightness) *
                  exp(contrast));
  }

}




## for single
void main() {
  emitGrayscale(toNormalized(getDataValue()));
}

# for 1st channel with the other ones color all controls
#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
#uicontrol float gamma slider(min=0.05, max=2.5, default=1, step=0.05)
#uicontrol float linlog slider(min=0, max=1, default=0, step=1)
void main() {
  float limit = 45000.0;
  float pix_val = toNormalized(getDataValue());
  if (linlog==1.0) {
  	pix_val = log(pix_val);
   	limit = 10.0;
  } else {
    pix_val = pow(pix_val,gamma);
    limit = 45000.0;
  }
  if(pix_val < min){
  	pix_val = 0.0;
  }
  if(pix_val > max){
    pix_val = 1.0;
  }

  if(invert==1.0){
  	  emitGrayscale((1.0 -(pix_val - brightness)) *
       exp(contrast));
  }
  else{
    emitGrayscale((pix_val + brightness) *
                  exp(contrast));
  }

}


## color channel 2 all controls
#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
#uicontrol float gamma slider(min=0.05, max=2.5, default=1, step=0.05)
#uicontrol float linlog slider(min=0, max=1, default=0, step=1)
void main() {
  float limit = 45000.0;
  // float pix_val = toNormalized(getDataValue());
  float pix_val = float(toRaw(getDataValue()));

  if (linlog==1.0) {
  	pix_val = log(pix_val);
   	limit = 10.0;
  } else {
    pix_val = pow(pix_val,gamma);
    limit = 45000.0;
  }


  pix_val = pix_val/limit;

  if(pix_val < min){
  	pix_val = 0.0;
  }
  if(pix_val > max){
    pix_val = 1.0;
  }

  if(invert==1.0){
  	  // emitGrayscale((1.0 -(pix_val - brightness)) *  exp(contrast));
    emitRGB(vec3((1.0 -(pix_val - brightness)) * exp(contrast),0,0));
  }
  else{
    // emitGrayscale((pix_val + brightness) *  exp(contrast));
     emitRGB(vec3((pix_val + brightness) * exp(contrast),0,0));
  }

}



## color channel 3 all controls
#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
#uicontrol float gamma slider(min=0.05, max=2.5, default=1, step=0.05)
#uicontrol float linlog slider(min=0, max=1, default=0, step=1)
void main() {
  float limit = 45000.0;
  float pix_val = float(toRaw(getDataValue()));

  if (linlog==1.0) {
  	pix_val = log(pix_val);
   	limit = 10.0;
  } else {
    pix_val = pow(pix_val,gamma);
    limit = 45000.0;
  }


  pix_val = pix_val/limit;

  if(pix_val < min){
  	pix_val = 0.0;
  }
  if(pix_val > max){
    pix_val = 1.0;
  }

  if(invert==1.0){
    emitRGB(vec3(0,(1.0 -(pix_val - brightness)) * exp(contrast),0));
  }
  else{
     emitRGB(vec3(0, (pix_val + brightness) * exp(contrast),0));
  }

}




# simple for structures
#uicontrol float brightness slider(min=-100, max=100)
#uicontrol float contrast slider(min=-30, max=30, step=1)
void main() {
  float pix_val = float(toRaw(getDataValue()));

    emitGrayscale((pix_val + brightness) *
                  exp(contrast));

}

# 4 channel

void main() {
    float v = toNormalized(getDataValue(0)) * 255.0;
    emitRGBA(vec4(v, 0.0, 0.0, v));
}



// add a histogram control for the current view
// get translation what is the number represent? everything should be in terms of microns and degrees.
// get names associated with shaped colors
// find midbrain, and move x microns from there to a landmark.
/*
MD589 settings
5um, 5um, 10um,
100nm 0.1 0 0
100nm 0 0.1 0
100nm 0 0 0.1 no translation


*/
look under MD585_filled
main info file specifies the names/info dir
names/info file key, value json file

https://s3.amazonaws.com/test-bucket-sid/final_precomputed_volumes/MD594
