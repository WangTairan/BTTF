import it.unimol.readability.metric.FeatureCalculator;
import it.unimol.readability.metric.code.CodeAnalyzer;
import it.unimol.readability.metric.parts.dorn.ColorsAreas;
import it.unimol.readability.metric.parts.dorn.DFTBandwidth;
import it.unimol.readability.metric.parts.dorn.VisualBandwidth2D;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Thin, language-aware adapter over the Dorn calculators bundled in rsm.jar. */
public final class DornFeatureServer {
    private static final String RESULT_PREFIX = "DORN_RESULT\t";

    private DornFeatureServer() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: DornFeatureServer <java|python|cuda>");
        }
        CodeAnalyzer.setImplementor(languageId(args[0]));
        FeatureCalculator[] calculators = calculators();

        BufferedReader input = new BufferedReader(
            new InputStreamReader(System.in, StandardCharsets.UTF_8)
        );
        String encoded;
        while ((encoded = input.readLine()) != null) {
            try {
                String source = new String(
                    Base64.getDecoder().decode(encoded),
                    StandardCharsets.UTF_8
                );
                StringBuilder result = new StringBuilder(RESULT_PREFIX).append("OK");
                for (FeatureCalculator calculator : calculators) {
                    calculator.setSource(source);
                    result.append('\t').append(Double.toString(calculator.calculate()));
                }
                System.out.println(result);
            } catch (Throwable error) {
                String message = error.getClass().getName()
                    + ": "
                    + String.valueOf(error.getMessage());
                String payload = Base64.getEncoder().encodeToString(
                    message.getBytes(StandardCharsets.UTF_8)
                );
                System.out.println(RESULT_PREFIX + "ERROR\t" + payload);
            }
            System.out.flush();
        }
    }

    private static int languageId(String language) {
        switch (language.trim().toLowerCase()) {
            case "java":
                return 1;
            case "python":
                return 2;
            case "cuda":
                return 3;
            default:
                throw new IllegalArgumentException("Unsupported Dorn language: " + language);
        }
    }

    private static FeatureCalculator[] calculators() {
        return new FeatureCalculator[] {
            new VisualBandwidth2D('X', "Identifiers"),
            new VisualBandwidth2D('X', "Comments"),
            new DFTBandwidth("Comments"),
            new DFTBandwidth("Numbers"),
            new DFTBandwidth("Indentations"),
            new ColorsAreas("Operators"),
            new VisualBandwidth2D('Y', "Identifiers")
        };
    }
}
