FROM alpine:3.20
# unbound-control e usado pelo agente para ler as estatisticas; se faltar, a construcao para aqui
RUN apk add --no-cache unbound && command -v unbound-control
COPY unbound.conf /etc/unbound/unbound.conf
EXPOSE 53/udp 53/tcp
CMD ["unbound", "-d", "-c", "/etc/unbound/unbound.conf"]
