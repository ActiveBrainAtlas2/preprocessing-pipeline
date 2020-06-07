#uicontrol float min slider(min=0, max=1, default=0)
#uicontrol float max slider(min=0, max=1, default=1)
#uicontrol float invert slider(min=0, max=1, default=0, step=1)
#uicontrol float brightness slider(min=-1, max=1)
#uicontrol float contrast slider(min=-3, max=3, step=0.01)
#uicontrol float gamma slider(min=0.05, max=2.5, default=1, step=0.05)
#uicontrol float linlog slider(min=0, max=1, default=0, step=1)

  void main() {
    float limit = 40000.0;
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


// add a histogram control for the current view
// get translation what is the number represent? everything should be in terms of microns and degrees.
// get names associated with shaped colors
// find midbrain, and move x microns from there to a landmark.
