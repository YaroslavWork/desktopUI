from fabric import Application, Fabricator


# lambda symbols
# f: is the fabricator itself, v: is the new value
counter_fabricator = Fabricator(
    interval=50,  # ms
    default_value=0,
    poll_from=lambda f: f.get_value() + 1,
    on_changed=lambda f, v: (
        (f.stop(), print("Counter Stopped"))
        if v == 43
        else print(f"Counter Value: {v}")
    ),
)

weather_fabricator = Fabricator(
    interval=1000 * 60,  # 1min
    poll_from="curl https://wttr.in/?format=Weather+in+%l:+%t+(Feels+Like+%f),+%C+%c",
    on_changed=lambda f, v: print(v.strip()),
)

player_fabricator = Fabricator(
    stream=True,
    poll_from="echo Hello",
    on_changed=lambda f, v: print(v.strip()),
)

documents_fabricator = Fabricator(
    interval=1000,  # 1 second
    poll_from="du -sh /home/galaxy/Documents/",  # NOTE: edit this
    on_changed=lambda f, v: print(f"Size of Documents: {v.split()[0]}"),
)

app = Application()
app.run()