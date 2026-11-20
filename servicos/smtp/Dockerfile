FROM alpine:3.20
RUN apk add --no-cache postfix \
 && addgroup -g 1000 caixa && adduser -D -H -u 1000 -G caixa caixa \
 && mkdir -p /var/mail/lab && chown -R caixa:caixa /var/mail/lab
COPY main.cf /etc/postfix/main.cf
EXPOSE 25
CMD ["postfix", "start-fg"]
