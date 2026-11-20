FROM alpine:3.20
RUN apk add --no-cache postfix
COPY main.cf /etc/postfix/main.cf
EXPOSE 25
CMD ["postfix", "start-fg"]
