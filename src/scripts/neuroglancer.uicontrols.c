/* channel 1 */
#uicontrol invlerp normalized
#uicontrol float gamma slider(min=0.05, max=2.5, default=1.0, step=0.05)

void main() {
    float pix =  normalized();
    pix = pow(pix,gamma);
      emitGrayscale(pix) ;
}

/* channel 2 */
#uicontrol invlerp normalized  (range=[0,45000])
#uicontrol float gamma slider(min=0.05, max=2.5, default=1.0, step=0.05)
#uicontrol bool colour checkbox(default=true)


  void main() {
    float pix =  normalized();
    pix = pow(pix,gamma);

    if (colour) {
       emitRGB(vec3(pix,0,0));
    } else {
      emitGrayscale(pix) ;
    }

}

/* channel 3 */
#uicontrol invlerp normalized  (range=[0,5000])
#uicontrol float gamma slider(min=0.05, max=2.5, default=1.0, step=0.05)
#uicontrol bool colour checkbox(default=true)

  void main() {
    float pix =  normalized();
    pix = pow(pix,gamma);

    if (colour){
       emitRGB(vec3(0, (pix),0));
    } else {
      emitGrayscale(pix) ;
    }

}
