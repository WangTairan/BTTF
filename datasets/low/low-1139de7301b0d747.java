package org.apache.commons.imaging.formats.tiff.photometricinterpreters;
import java.io.IOException;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.common.ImageBuilder;

public class PhotometricInterpreterPalette extends PhotometricInterpreter {
   private final int[] indexColorMap;

   public PhotometricInterpreterPalette(int samplesPerPixel, int[] bitsPerSample, int predictor, int width, int height, int[] colorMap) {
      super(samplesPerPixel, bitsPerSample, predictor, width, height);
      int bitsPerPixel = this.bitsPerSample[0];
      int colormapScale = 1 << bitsPerPixel;
      this.indexColorMap = new int[colormapScale];

      for(int index = 0; index < colormapScale; ++index) {
         int red = colorMap[index] >> 8 & 255;
         int green = colorMap[index + colormapScale] >> 8 & 255;
         int blue = colorMap[index + 2 * colormapScale] >> 8 & 255;
         this.indexColorMap[index] = -16777216 | red << 16 | green << 8 | blue;
      }

   }

   public void interpretPixel(ImageBuilder imageBuilder, int[] samples, int x, int y) throws ImageReadException, IOException {
      imageBuilder.setRGB(x, y, this.indexColorMap[samples[0]]);
   }
}
