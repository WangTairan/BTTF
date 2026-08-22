package org.joda.time.format;
import java.io.IOException;
import java.io.Writer;
import java.util.Locale;
import org.joda.time.MutablePeriod;
import org.joda.time.Period;
import org.joda.time.PeriodType;
import org.joda.time.ReadWritablePeriod;
import org.joda.time.ReadablePeriod;

public class PeriodFormatter {
   private final PeriodPrinter iPrinter;
   private final PeriodParser iParser;
   private final Locale iLocale;
   private final PeriodType iParseType;

   public PeriodFormatter(PeriodPrinter var1, PeriodParser var2) {
      this.iPrinter = var1;
      this.iParser = var2;
      this.iLocale = null;
      this.iParseType = null;
   }

   private PeriodFormatter(PeriodPrinter var1, PeriodParser var2, Locale var3, PeriodType var4) {
      this.iPrinter = var1;
      this.iParser = var2;
      this.iLocale = var3;
      this.iParseType = var4;
   }

   public boolean isPrinter() {
      return this.iPrinter != null;
   }

   public PeriodPrinter getPrinter() {
      return this.iPrinter;
   }

   public boolean isParser() {
      return this.iParser != null;
   }

   public PeriodParser getParser() {
      return this.iParser;
   }

   public PeriodFormatter withLocale(Locale var1) {
      return var1 != this.getLocale() && (var1 == null || !var1.equals(this.getLocale())) ? new PeriodFormatter(this.iPrinter, this.iParser, var1, this.iParseType) : this;
   }

   public Locale getLocale() {
      return this.iLocale;
   }

   public PeriodFormatter withParseType(PeriodType var1) {
      return var1 == this.iParseType ? this : new PeriodFormatter(this.iPrinter, this.iParser, this.iLocale, var1);
   }

   public PeriodType getParseType() {
      return this.iParseType;
   }

   public void printTo(StringBuffer var1, ReadablePeriod var2) {
      this.checkPrinter();
      this.checkPeriod(var2);
      this.getPrinter().printTo(var1, var2, this.iLocale);
   }

   public void printTo(Writer var1, ReadablePeriod var2) throws IOException {
      this.checkPrinter();
      this.checkPeriod(var2);
      this.getPrinter().printTo(var1, var2, this.iLocale);
   }

   public String print(ReadablePeriod var1) {
      this.checkPrinter();
      this.checkPeriod(var1);
      PeriodPrinter var2 = this.getPrinter();
      StringBuffer var3 = new StringBuffer(var2.calculatePrintedLength(var1, this.iLocale));
      var2.printTo(var3, var1, this.iLocale);
      return var3.toString();
   }

   private void checkPrinter() {
      if (this.iPrinter == null) {
         throw new UnsupportedOperationException("Printing not supported");
      }
   }

   private void checkPeriod(ReadablePeriod var1) {
      if (var1 == null) {
         throw new IllegalArgumentException("Period must not be null");
      }
   }

   public int parseInto(ReadWritablePeriod var1, String var2, int var3) {
      this.checkParser();
      this.checkPeriod(var1);
      return this.getParser().parseInto(var1, var2, var3, this.iLocale);
   }

   public Period parsePeriod(String var1) {
      this.checkParser();
      return this.parseMutablePeriod(var1).toPeriod();
   }

   public MutablePeriod parseMutablePeriod(String var1) {
      this.checkParser();
      MutablePeriod var2 = new MutablePeriod(0L, this.iParseType);
      int var3 = this.getParser().parseInto(var2, var1, 0, this.iLocale);
      if (var3 >= 0) {
         if (var3 >= var1.length()) {
            return var2;
         }
      } else {
         var3 = ~var3;
      }

      throw new IllegalArgumentException(FormatUtils.createErrorMessage(var1, var3));
   }

   private void checkParser() {
      if (this.iParser == null) {
         throw new UnsupportedOperationException("Parsing not supported");
      }
   }
}
