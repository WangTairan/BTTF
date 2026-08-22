package org.apache.commons.imaging.palette;
import java.util.List;
import org.apache.commons.imaging.ImageWriteException;

public class QuantizedPalette extends Palette {
   private final int precision;
   private final List<ColorSpaceSubset> subsets;
   private final ColorSpaceSubset[] straight;

   public QuantizedPalette(List<ColorSpaceSubset> subsets, int precision) {
      this.subsets = subsets;
      this.precision = precision;
      this.straight = new ColorSpaceSubset[1 << precision * 3];

      for(int i = 0; i < subsets.size(); ++i) {
         ColorSpaceSubset subset = (ColorSpaceSubset)subsets.get(i);
         subset.setIndex(i);

         for(int u = subset.mins[0]; u <= subset.maxs[0]; ++u) {
            for(int j = subset.mins[1]; j <= subset.maxs[1]; ++j) {
               for(int k = subset.mins[2]; k <= subset.maxs[2]; ++k) {
                  int index = u << precision * 2 | j << precision * 1 | k << precision * 0;
                  this.straight[index] = subset;
               }
            }
         }
      }

   }

   public int getPaletteIndex(int rgb) throws ImageWriteException {
      int precisionMask = (1 << this.precision) - 1;
      int index = rgb >> 24 - 3 * this.precision & precisionMask << (this.precision << 1) | rgb >> 16 - 2 * this.precision & precisionMask << this.precision | rgb >> 8 - this.precision & precisionMask;
      return this.straight[index].getIndex();
   }

   public int getEntry(int index) {
      ColorSpaceSubset subset = (ColorSpaceSubset)this.subsets.get(index);
      return subset.rgb;
   }

   public int length() {
      return this.subsets.size();
   }
}
