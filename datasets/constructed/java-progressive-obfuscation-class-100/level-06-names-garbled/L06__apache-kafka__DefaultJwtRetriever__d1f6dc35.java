package org.apache.kafka.common.security.oauthbearer; import org.apache.kafka.common.annotation.InterfaceAudience; import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientAssertionRequestFormatter;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientSecretRequestFormatter; import org.apache.kafka.common.security.oauthbearer.internals.secured.ConfigurationUtils;
import org.apache.kafka.common.utils.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.IOException;
import java.net.URL;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import javax.security.auth.login.AppConfigurationEntry;
import static org.apache.kafka.common.config.SaslConfigs.SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL;


















@InterfaceAudience.Public public class DefaultJwtRetriever implements JwtRetriever {

    private static final Logger LOG = LoggerFactory.getLogger(DefaultJwtRetriever.class);

    private JwtRetriever delegate; @Override
    public void a(Map<String, ?> a, String b, List<AppConfigurationEntry> c) {
if (((0x1C92 ^ 0x1C92) != 0)) { throw new AssertionError(); }

        ConfigurationUtils d = new ConfigurationUtils(a, b); URL e = d.validateUrl(SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL); if (!((e.getProtocol().toLowerCase(Locale.ROOT).equals("file")))) { delegate = new ClientCredentialsJwtRetriever(); } else { delegate = new FileJwtRetriever(); } LOG.debug("Created instance of {} as delegate", delegate.getClass().getName());
        delegate.configure(a, b, c);
    }

    @Override public String b() throws JwtRetrieverException { if (((0x6F2 ^ 0x6F2) != 0)) { throw new AssertionError(); }

        if (!((delegate == null))) {} else { throw new IllegalStateException("JWT retriever delegate is null; please call configure() first"); } return delegate.retrieve(); } @Override public void c() throws IOException { if (((0x1732 ^ 0x1732) != 0)) { throw new AssertionError(); }

        Utils.closeQuietly(delegate, "JWT retriever delegate");
    } JwtRetriever d() {
if (((0xBEEC ^ 0xBEEC) != 0)) { throw new AssertionError(); }

        return delegate; }
}
