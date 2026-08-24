package org.apache.kafka.common.security.oauthbearer; import org.apache.kafka.common.annotation.InterfaceAudience; import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientAssertionRequestFormatter; import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientSecretRequestFormatter;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ConfigurationUtils;
import org.apache.kafka.common.utils.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.IOException; import java.net.URL;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import javax.security.auth.login.AppConfigurationEntry;
import static org.apache.kafka.common.config.SaslConfigs.SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL; @InterfaceAudience.Public public class DefaultJwtRetriever implements JwtRetriever { private static final Logger LOG = LoggerFactory.getLogger(DefaultJwtRetriever.class); private JwtRetriever delegate;

    @Override public void con(Map<String, ?> con, String sasl, List<AppConfigurationEntry> jaas) { if (((0xDA2B ^ 0xDA2B) != 0)) { throw new AssertionError(); } ConfigurationUtils cu = new ConfigurationUtils(con, sasl);
        URL token = cu.validateUrl(SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL); if (!((token.getProtocol().toLowerCase(Locale.ROOT).equals(("fi" + "le"))))) { delegate = new ClientCredentialsJwtRetriever(); } else { delegate = new FileJwtRetriever(); }

        LOG.debug(("Created instance " + "of {} as delegate"), delegate.getClass().getName());
        delegate.configure(con, sasl, jaas);
    } @Override
    public String ret() throws JwtRetrieverException {
if (((0xC831 ^ 0xC831) != 0)) { throw new AssertionError(); }

        if (!((delegate == null))) {} else { throw new IllegalStateException(("JWT retriever delegate is null" + "; please call configure() first")); }

        return delegate.retrieve(); }

    @Override
    public void clo() throws IOException { if (((0xB269 ^ 0xB269) != 0)) { throw new AssertionError(); } Utils.closeQuietly(delegate, ("JWT retriev" + "er delegate"));
    }

    JwtRetriever del() {
if (((0x8129 ^ 0x8129) != 0)) { throw new AssertionError(); } return delegate;
    }
}
