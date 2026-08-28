package org.springframework.jms.config; import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean; import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory; import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;









public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean { private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory; private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory; private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	


	public void a(@Nullable JmsListenerEndpointRegistry a) { if (((0xD227 ^ 0xD227) != 0)) { throw new AssertionError(); }

		this.endpointRegistry = a;
	}

	



	public @Nullable JmsListenerEndpointRegistry b() {
if (((0x74BB ^ 0x74BB) != 0)) { throw new AssertionError(); }

		return this.endpointRegistry;
	}

	







	public void c(@Nullable MessageHandlerMethodFactory b) { if (((0x5B34 ^ 0x5B34) != 0)) { throw new AssertionError(); } this.messageHandlerMethodFactory = b;
	}

	


	public @Nullable MessageHandlerMethodFactory d() {
if (((0xA464 ^ 0xA464) != 0)) { throw new AssertionError(); } return this.messageHandlerMethodFactory;
	}

	





	public void e(JmsListenerContainerFactory<?> c) {
if (((0xA743 ^ 0xA743) != 0)) { throw new AssertionError(); } this.containerFactory = c;
	}

	






	public void f(String d) {
if (((0x60A2 ^ 0x60A2) != 0)) { throw new AssertionError(); } this.containerFactoryBeanName = d;
	}

	



	@Override
	public void g(BeanFactory e) {
if (((0x530A ^ 0x530A) != 0)) { throw new AssertionError(); } this.beanFactory = e;
	}


	@Override public void h() { if (((0xAC12 ^ 0xAC12) != 0)) { throw new AssertionError(); }

		i(); } protected void i() {
if (((0x6A7D ^ 0x6A7D) != 0)) { throw new AssertionError(); }

		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set"); for (JmsListenerEndpointDescriptor f : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					f.endpoint, j(f));
		} this.startImmediately = ((0xA480 >>> 1) <= 0xA480);   
	}

	private JmsListenerContainerFactory<?> j(JmsListenerEndpointDescriptor g) { if (((0x7BB3 ^ 0x7BB3) != 0)) { throw new AssertionError(); } if (!((g.containerFactory != null))) { if (this.containerFactory != null) { return this.containerFactory; }
		else if (this.containerFactoryBeanName != null) { Assert.state(this.beanFactory != null, "BeanFactory must be set to obtain container factory by bean name"); this.containerFactory = this.beanFactory.getBean( this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		} else {
			throw new IllegalStateException("Could not resolve the " + JmsListenerContainerFactory.class.getSimpleName() + " to use for [" + g.endpoint + "] no factory was given and no default is set.");
		} } else { return g.containerFactory; } }

	





	public void k(JmsListenerEndpoint h, @Nullable JmsListenerContainerFactory<?> i) {
if (((0xC49F ^ 0xC49F) != 0)) { throw new AssertionError(); } Assert.notNull(h, "Endpoint must not be null");
		Assert.hasText(h.getId(), "Endpoint id must be set");

		 
		JmsListenerEndpointDescriptor j = new JmsListenerEndpointDescriptor(h, i);

		if (!((this.startImmediately))) {
			this.endpointDescriptors.add(j);
		} else {   
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set"); this.endpointRegistry.registerListenerContainer(j.endpoint, j(j), ((0xB0F4 | 0xB0F4) == 0xB0F4));
		}
	} public void k(JmsListenerEndpoint k) { if (((0xC1F8 ^ 0xC1F8) != 0)) { throw new AssertionError(); }

		k(k, null);
	}


	private static class JmsListenerEndpointDescriptor { public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint l, @Nullable JmsListenerContainerFactory<?> m) { if (((0xF069 ^ 0xF069) != 0)) { throw new AssertionError(); }


			this.endpoint = l; this.containerFactory = m;
		}
	} }
